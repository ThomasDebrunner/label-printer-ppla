import argparse
import usb.core
import sys
from ppla import PPLA, ppla_hex
from PIL import Image


def error(msg):
    print(msg, file=sys.stderr)
    exit(1)


class Printer:
    CLASS_REQUEST_GET_DEVICE_ID = 0x00
    CLASS_REQUEST_GET_PORT_STATUS = 0x01
    CLASS_REQUEST_SOFT_RESET = 0x02

    def __init__(self, vendor_id, product_id):
        self._dev = None
        self._vendor_id = vendor_id
        self._product_id = product_id
        self._ep_in = None
        self._ep_out = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open(self):
        self._dev = usb.core.find(idVendor=self._vendor_id, idProduct=self._product_id)
        if self._dev is None:
            error('Device not found')
        self._dev.set_configuration()

        # find endpoints
        cfg = self._dev.get_active_configuration()
        intf = cfg[(0, 0)]
        self._ep_out = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )
        if self._ep_out is None:
            error('Endpoint OUT not found')
        self._ep_in = usb.util.find_descriptor(
            intf,
            # match the first IN endpoint
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        )
        if self._ep_in is None:
            error('Endpoint IN not found')

    def close(self):
        if self._dev is not None:
            usb.util.dispose_resources(self._dev)
            self._dev = None
            self._ep_in = None
            self._ep_out = None

    def _perform_class_request(self, request, value, index, length):
        request_type = usb.util.build_request_type(
            direction=usb.util.CTRL_IN,
            type=usb.util.CTRL_TYPE_CLASS,
            recipient=usb.util.CTRL_RECIPIENT_INTERFACE
        )
        return self._dev.ctrl_transfer(request_type, request, value, index, length)

    def get_device_id(self):
        data = self._perform_class_request(
            self.CLASS_REQUEST_GET_DEVICE_ID,
            value=0,
            index=0,
            length=64
        )
        return ''.join([chr(c) for c in data])

    def get_port_status(self):
        data = self._perform_class_request(
            self.CLASS_REQUEST_GET_PORT_STATUS,
            value=0,
            index=0,
            length=1
        )
        result = {
            'paper_empty': bool(data[0] & (1 << 5)),
            'select': bool(data[0] & (1 << 4)),
            'error': not bool(data[0] & (1 << 3)),
        }
        return result

    def soft_reset(self):
        data = self._perform_class_request(
            self.CLASS_REQUEST_SOFT_RESET,
            value=0,
            index=0,
            length=0
        )
        return data

    def send(self, data):
        offset = 0
        size = len(data)
        while offset < size:
            write_size = self._ep_out.wMaxPacketSize
            if offset + write_size > size:
                write_size = size - offset
            length = self._dev.write(self._ep_out.bEndpointAddress, data[offset:offset + write_size])
            if length <= 0:
                raise RuntimeError("USB bulk write error")
            offset += length
        return offset

    def recv(self, length):
        return self._ep_in.read(length)


def main():
    parser = argparse.ArgumentParser(description='Argox Label Printer Tool')
    parser.add_argument('--product-id', type=int, help='Product ID of the printer', default=0x032a)
    parser.add_argument('--vendor-id', type=int, help='Vendor ID of the printer', default=0x1664)
    args = parser.parse_args()

    # find our device
    with Printer(args.vendor_id, args.product_id) as p:
        print(p.get_device_id())
        print(p.get_port_status())
        print(p.soft_reset())

        tux_hex = ppla_hex(Image.open('tux.jpg'))

        ppla = PPLA()
        ppla.clear_memory(memory='ram')
        ppla.set_transfer_type('direct-thermal')
        ppla.set_label_length_inch(2.65)
        ppla.download_graphics('TUX', ppla_hex=tux_hex, memory='ram')
        ppla.enter_label_mode()
        ppla.label_set_pixel_size()
        ppla.label_graphic(100, 16, 'TUX')
        ppla.label_text(100, 2, 'Hello World!', font='asd-12')
        ppla.label_barcode(260, 40, 'A' + 'TUX', barcode_type='code-128', orientation='landscape')
        ppla.label_end_job()

        # perform print
        p.send(ppla.get_bytes())

if __name__ == '__main__':
    main()




