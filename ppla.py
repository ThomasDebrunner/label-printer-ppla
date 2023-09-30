
import sys
import re
import datetime
from PIL import Image, ImageOps


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# For some strange reason, the HEX format does not directly map pixels to bits. 
# It does so for the lower 4 bits in each byte, but the higher 4 bytes follow some strange encoding scheme. 
# I managed to reverse engineer it by doing many test prints, but I have no idea why it is the way it is.
PPLA_HEX_MAP = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0xea, 0xeb, 0xec, 0xed, 0xee, 0xef, 0x10,
                0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0xfa, 0xfb, 0xfc, 0xfd, 0xfe, 0xff, 0x20, 0x21,
                0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x30, 0x31, 0x32,
                0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x40, 0x41, 0x42, 0x43,
                0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x2a, 0x2b, 0x2c, 0x2d, 0x2e, 0x2f, 0x50, 0x51, 0x52, 0x53, 0x54,
                0x55, 0x56, 0x57, 0x58, 0x59, 0x3a, 0x3b, 0x3c, 0x3d, 0x3e, 0x3f, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65,
                0x66, 0x67, 0x68, 0x69, 0x4a, 0x4b, 0x4c, 0x4d, 0x4e, 0x4f, 0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76,
                0x77, 0x78, 0x79, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87,
                0x88, 0x89, 0x6a, 0x6b, 0x6c, 0x6d, 0x6e, 0x6f, 0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98,
                0x99, 0x7a, 0x7b, 0x7c, 0x7d, 0x7e, 0x7f, 0xa0, 0xa1, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6, 0xa7, 0xa8, 0xa9,
                0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f, 0xb0, 0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0x9a,
                0x9b, 0x9c, 0x9d, 0x9e, 0x9f, 0xc0, 0xc1, 0xc2, 0xc3, 0xc4, 0xc5, 0xc6, 0xc7, 0xc8, 0xc9, 0xaa, 0xab,
                0xac, 0xad, 0xae, 0xaf, 0xd0, 0xd1, 0xd2, 0xd3, 0xd4, 0xd5, 0xd6, 0xd7, 0xd8, 0xd9, 0xba, 0xbb, 0xbc,
                0xbd, 0xbe, 0xbf, 0xe0, 0xe1, 0xe2, 0xe3, 0xe4, 0xe5, 0xe6, 0xe7, 0xe8, 0xe9, 0xca, 0xcb, 0xcc, 0xcd,
                0xce, 0xcf, 0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9, 0xda, 0xdb, 0xdc, 0xdd, 0xde,
                0xdf]


def ppla_hex(image : Image):
    image = image.convert('1')
    image = ImageOps.mirror(image.rotate(180))
    width, height = image.size
    usable_width = width - (width % 8)
    result = bytearray()
    for y in range(0, height):
        result += b'80' + '{:02x}'.format(usable_width // 8).encode('ascii')
        for x in range(0, usable_width, 8):
            byte = 0
            for i in range(0, 8):
                if image.getpixel((x + i, y)) < 127:
                    byte |= 1 << (7 - i)
            result += '{:02x}'.format(PPLA_HEX_MAP[byte]).encode('ascii')
    result += b'FFFF'
    return result


class PPLA:
    SOH = b'\x01'
    STX = b'\x02'
    ESC = b'\x1b'

    _fonts = {
        'font-0': (b'0', b'000'),
        'font-1': (b'1', b'000'),
        'font-2': (b'2', b'000'),
        'font-3': (b'3', b'000'),
        'font-4': (b'4', b'000'),
        'font-5': (b'5', b'000'),
        'font-6': (b'6', b'000'),
        'font-7': (b'7', b'000'),
        'font-8': (b'8', b'000'),
        'asd-4': (b'9', b'000'),
        'asd-6': (b'9', b'001'),
        'asd-8': (b'9', b'002'),
        'asd-10': (b'9', b'003'),
        'asd-12': (b'9', b'004'),
        'asd-14': (b'9', b'005'),
        'asd-16': (b'9', b'006'),
        'courier-roman8': (b':', b'000'),
        'courier-ecma94': (b':', b'001'),
        'courier-pc': (b':', b'002'),
        'courier-pc-a': (b':', b'003'),
        'courier-pc-b': (b':', b'004'),
        'legal': (b':', b'005'),
        'greek': (b':', b'006'),
        'russian': (b':', b'007'),
    }

    _orientations = {
        'portrait': b'1',
        'landscape': b'4',
        'reverse-portrait': b'3',
        'reverse-landscape': b'2'
    }

    _scales = {
        0: b'0',
        1: b'1',
        2: b'2',
        3: b'3',
        4: b'4',
        5: b'5',
        6: b'6',
        7: b'7',
        8: b'8',
        9: b'9',
        10: b'A',
        11: b'B',
        12: b'C',
        13: b'D',
        14: b'E',
        15: b'F',
        16: b'G',
        17: b'H',
        18: b'I',
        19: b'J',
        20: b'K',
        21: b'L',
        22: b'M',
        23: b'N',
        24: b'O',
    }

    _transfer_types = {
        'direct-thermal': b'0',
        'thermal-transfer': b'1',
    }

    _barcode_types = {
        'code-39': (b'A', b'a'),
        'upc-a': (b'B', b'b'),
        'upc-e': (b'C', b'c'),
        'i25': (b'D', b'd'),
        'code-128': (b'E', b'e'),
        'ean-13': (b'F', b'f'),
        'ean-8': (b'G', b'g'),
        'hbic': (b'H', b'h'),
        'codabar': (b'I', b'i'),
        'ji-2of5': (b'J', b'j'),
        'plessey': (b'K', b'k'),
        'i25-checksum-bearer': (b'L', b'l'),
        'upc2': (b'M', b'm'),
        'upc5': (b'N', b'n'),
        'code-93': (b'O', b'o'),
        'postnet': (None, b'p'),
        'ucc-ean-128': (b'Q', b'q'),
        'ucc-ean-128-kmart': (b'R', b'r'),
        'telepen': (b'T', b't'),
        'fim': (None, b'v'),
        'maxicode': (None, b'u'),
        'pdf-417': (None, b'z'),
    }

    _label_feed_rates = {
        '1.0': b'A',
        '1.5': b'B',
        '2.0': b'C',
        '2.5': b'D',
        '3.0': b'E',
        '3.5': b'F',
        '4.0': b'G',
        '4.5': b'H',
        '5.0': b'I',
        '5.5': b'J',
        '6.0': b'K',
    }

    _memory_types = {
        'ram': b'A',
        'flash': b'B'
    }

    def _check_in_options(self, selection, option_dict):
        if selection in option_dict:
            return option_dict[selection]
        else:
            print('Invalid selection: ' + selection)
            print('Valid selections are: ' + ', '.join(option_dict.keys()))
            raise ValueError('Invalid selection')

    def __init__(self):
        self._data = bytearray()

    def reset(self):
        self._data += self.SOH + b'#\r'
        return self

    def request_status(self):
        self._data += self.SOH + b'A\r'
        return self

    def toggle_pause(self):
        self._data += self.SOH + b'B\r'
        return self

    def set_date_time(self, date_time=None):
        if date_time is None:
            date_time = datetime.datetime.now()
        self._data += self.STX + b'A' + date_time.strftime('%w%m%d%H%M%j').encode('ascii') + b'\r'
        return self

    def enable_label_echo_character(self):
        self._data += self.STX + b'a\r'
        return self

    def dump_memory_content(self, address):
        address = '{:07X}'.format(address)
        self._data += self.STX + b'D' + address.encode('ascii') + b'\r'

    def feed_label(self):
        self._data += self.STX + b'F\r'
        return self

    def set_stop_position_and_automatic_backfeed_inch(self, backfeed):
        backfeed = '{:03d}'.format(int(backfeed * 100))
        self._data += self.STX + b'f' + backfeed.encode('ascii') + b'\r'

    def print_stored_label(self, count):
        count = '{:04d}'.format(count)
        self._data += self.STX + b'E' + count.encode('ascii') + b'\r'
        self._data += self.STX + b'G\r'

    def set_label_feed_rate(self, rate):
        rate = self._check_in_options(rate, self._label_feed_rates)
        self._data += self.STX + b'S' + rate + b'\r'
        return self

    def print_test_pattern(self):
        self._data += self.STX + b'T\r'
        return self

    def replace_form_data(self, field_number, data):
        field_number = '{:02d}'.format(field_number)
        self._data += self.STX + b'U' + field_number.encode('ascii') + data.encode('ascii') + b'\r'
        return self

    def enable_cutter_dispenser(self):
        self._data += self.STX + b'V1\r'
        return self

    def disable_cutter_dispenser(self):
        self._data += self.STX + b'V0\r'
        return self

    def inquire_printer_version(self):
        self._data += self.STX + b'v\r'
        return self

    def inquire_font_memory_status(self):
        self._data += self.STX + b'WF\r'
        return self

    def inquire_graphics_memory_status(self):
        self._data += self.STX + b'WG\r'
        return self

    def inquire_label_memory_status(self):
        self._data += self.STX + b'WL\r'
        return self

    def set_pause_after_each_label(self):
        self._data += self.STX + b'J\r'
        return self

    def cancel_pause_after_each_label(self):
        self._data += self.STX + b'j\r'
        return self

    def inquire_system_configuration(self):
        self._data += self.STX + b'KQ\r'
        return self

    def set_reflective_sensor(self):
        self._data += self.STX + b'r\r'
        return self

    def set_transparent_sensor(self):
        self._data += self.STX + b'e\r'
        return self

    def enter_label_mode(self):
        self._data += self.STX + b'L\r'
        return self

    def set_transfer_type(self, transfer_type):
        transfer_type = self._check_in_options(transfer_type, self._transfer_types)
        self._data += self.STX + b'KI7' + transfer_type + b'\r'
        return self

    def set_max_label_length_inch(self, length):
        length = '{:04d}'.format(int(length * 100)).encode('ascii')
        self._data += self.STX + b'M' + length + b'\r'
        return self

    def set_label_length_inch(self, length):
        length = '{:04d}'.format(int(length * 100)).encode('ascii')
        self._data += self.STX + b'c' + length + b'\r'
        return self

    def set_print_start_position_inches(self, print_start_position):
        print_start_position = '{:04d}'.format(int(print_start_position * 100)).encode('ascii')
        self._data += self.STX + b'O' + print_start_position + b'\r'
        return self

    def enter_data_dump_mode(self):
        self._data += self.STX + b'P\r'
        return self

    def clear_all_memory(self):
        self._data += self.STX + b'Q\r'
        return self

    def clear_memory(self, memory='ram'):
        memory = self._check_in_options(memory, self._memory_types)
        self._data += self.STX + b'q' + memory + b'\r'
        return self

    def clear_ram_memory(self):
        self._data += self.STX + b'qA\r'
        return self

    def measurements_in_inches(self):
        self._data += self.STX + b'n\r'

    def download_graphics(self, name, ppla_hex, memory='ram'):
        memory = self._check_in_options(memory, self._memory_types)
        name = name.encode('ascii')
        assert len(name) <= 16
        self._data += self.STX + b'I' + memory + b'F' + name + b'\r' + ppla_hex + b'\r'

    def label_set_cut_by_amount(self, amount):
        amount = '{:04d}'.format(int(amount * 100))
        self._data += b':' + amount.encode('ascii') + b'\r'

    def label_set_xor_printing(self):
        self._data += b'A1\r'

    def label_set_or_printing(self):
        self._data += b'A2\r'

    def label_set_left_margin_inch(self, margin):
        margin = '{:04d}'.format(int(margin * 100))
        self._data += b'C' + margin.encode('ascii') + b'\r'

    def label_set_pixel_size(self, width=b'1', height=b'1'):
        self._data += b'D' + width + height + b'\r'

    def label_end_job(self):
        self._data += b'E\r'
        return self

    def label_store_previous_to_global_register(self):
        self._data += b'G\r'
        return self

    def label_retreive_from_global_register(self, register='A'):
        self._data += b'S' + register.encode('ascii') + b'\r'

    def label_set_heat_value(self, heat_value):
        assert 2 <= heat_value <= 20
        heat_value = '{:02d}'.format(heat_value)
        self._data += b'H' + heat_value.encode('ascii') + b'\r'

    def label_toggle_mirror_mode(self):
        self._data += b'M\r'

    def label_set_print_speed(self, speed):
        speed = self._check_in_options(speed, self._label_feed_rates)
        self._data += b'P' + speed + b'\r'

    def label_set_quantity(self, quantity):
        quantity = '{:04d}'.format(quantity)
        self._data += b'Q' + quantity.encode('ascii') + b'\r'

    def label_set_vertical_offset_inch(self, offset):
        offset = '{:04d}'.format(int(offset * 100))
        self._data += b'V' + offset.encode('ascii') + b'\r'

    def label_normal_zero(self):
        self._data += b'z\r'

    def label_date_and_time(self, format):
        self._data += b'T' + format.encode('ascii') + b'\r'

    def label_text(self, x, y, data, orientation='portrait', font='font-4', horizontal_scale=1, vertical_scale=1):
        if isinstance(data, str):
            data = data.encode('ascii')
        orientation = self._check_in_options(orientation, self._orientations)
        font_type, font_subtype = self._check_in_options(font, self._fonts)
        h_scale = self._check_in_options(horizontal_scale, self._scales)
        v_scale = self._check_in_options(vertical_scale, self._scales)

        x = '{:04d}'.format(x).encode('ascii')
        y = '{:04d}'.format(y).encode('ascii')

        self._data += orientation + font_type + h_scale + v_scale + font_subtype + y + x + data + b'\r'
        return self

    def label_barcode(self, x, y, data, orientation='portrait', barcode_type='code-128', wide_bar_width=5, narrow_bar_width=2, height=0, human_readable=False):
        orientation = self._check_in_options(orientation, self._orientations)
        barcode_type_readable, barcode_type_non_readable = self._check_in_options(barcode_type, self._barcode_types)
        x = '{:04d}'.format(x).encode('ascii')
        y = '{:04d}'.format(y).encode('ascii')
        height = '{:03d}'.format(int(height)).encode('ascii')
        wide_bar_width = '{:01}'.format(int(wide_bar_width)).encode('ascii')
        narrow_bar_width = '{:01d}'.format(int(narrow_bar_width)).encode('ascii')

        barcode_type = barcode_type_readable if human_readable else barcode_type_non_readable
        if barcode_type is None:
            raise ValueError('Invalid barcode type')

        self._data += orientation + barcode_type + wide_bar_width + narrow_bar_width + height + y + x + data.encode('ascii') + b'\r'
        return self

    def label_box(self, x, y, width, height, orientation='portrait', top_bottom_thickness=2, left_right_thickness=2):
        orientation = self._check_in_options(orientation, self._orientations)
        top_bottom_thickness = '{:03d}'.format(int(top_bottom_thickness)).encode('ascii')
        left_right_thickness = '{:03d}'.format(int(left_right_thickness)).encode('ascii')
        x = '{:04d}'.format(x).encode('ascii')
        y = '{:04d}'.format(y).encode('ascii')
        width = '{:03d}'.format(width).encode('ascii')
        height = '{:03d}'.format(height).encode('ascii')
        self._data += orientation + b'X11000' + y + x + b'B' + width + height + top_bottom_thickness + left_right_thickness + b'\r'
        return self

    def label_line(self, x, y, width, height, orientation='portrait'):
        orientation = self._check_in_options(orientation, self._orientations)
        x = '{:04d}'.format(x).encode('ascii')
        y = '{:04d}'.format(y).encode('ascii')
        width = '{:03d}'.format(width).encode('ascii')
        height = '{:03d}'.format(height).encode('ascii')
        self._data += orientation + b'X11000' + y + x + b'L' + width + height + b'\r'
        return self

    def label_graphic(self, x, y, name, orientation='portrait'):
        orientation = self._check_in_options(orientation, self._orientations)
        x = '{:04d}'.format(x).encode('ascii')
        y = '{:04d}'.format(y).encode('ascii')
        self._data += orientation + b'Y11000' + y + x + name.encode('ascii') + b'\r'
        return self

    def get_bytes(self):
        return self._data
