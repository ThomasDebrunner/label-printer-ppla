

data = [
(6,  0b0001),
(10, 0b1111),
(6,  0b0000),
(10, 0b1110),
(6,  0b1111),
(10, 0b1101),
(6,  0b1110),
(10, 0b1100),
(6,  0b1101),
(10, 0b1011),
(6,  0b1100),
(10, 0b1010),
(6,  0b1011),
(10, 0b1001),
(6,  0b1010),
(10, 0b1000),
(6,  0b1001),
(10, 0b0111),
(6,  0b1000),
(10, 0b0110),
(6,  0b0111),
(10, 0b0101),
(6,  0b0110),
(10, 0b0100),
(6,  0b0101),
(10, 0b0011),
(6,  0b0100),
(10, 0b0010),
(6,  0b0011),
(10, 0b0001),
(6,  0b0010),
(10, 0b0000),
]

codes = {}
j = 0
for c, p in reversed(data):
    for i in range(c):
        code = p << 4 | (j & 0xF)
        # print('0x%02x, // %d' % (code, j))
        codes[code] = j
        j += 1
        # print(j)

for k in sorted(codes.keys()):
    print('0x%02x, // %d' % (codes[k], k))
#     s += c

# for k, v in patterns.items():
#     print(k, v)


# print(s)





# 0b1111 + 0b0010 = 0b0001
# 0b1110 + 0b0010 = 0b0000
# 0b1101 + 0b0010 = 0b1111
# 0b1100 + 0b0010 = 0b1110
# 0b1011 + 0b0010 = 0b1101
# 0b1010 + 0b0010 = 0b1100
# 0b1001 + 0b0010 = 0b1011
# 0b1000 + 0b0010 = 0b1010
# 0b0111 + 0b0010 = 0b1001
# 0b0110 + 0b0010 = 0b1000
# 0b0101 + 0b0010 = 0b0111
# 0b0100 + 0b0010 = 0b0110
# 0b0011 + 0b0010 = 0b0101
# 0b0010 + 0b0010 = 0b0100
# 0b0001 + 0b0010 = 0b0011
# 0b0000 + 0b0010 = 0b0010

