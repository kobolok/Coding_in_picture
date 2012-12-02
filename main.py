# -*- coding: utf-8 -*- 
def main():
    args = args_parser()
    if args["a"]:
        archive_name = packing(args["path"])
        bin_code = coding(archive_name)
        making_bmp(bin_code, args["resultimage"])
    else:
        blocks = decoding_image(args["image"])
        archive_name = restoring_archive(blocks)
        unpacking(archive_name, args["resultpath"])

def args_parser():
    import argparse

    parser = argparse.ArgumentParser(description="Сохранение и восстановление файлов в изображении с помехоустойчивым кодированием")
    parser.add_argument("-a", action="store_true", help="Нужен режим архивирования и кодирование.")
    parser.add_argument("path", nargs="?", type=str, help="Путь до файла или папки, которую требуется заархивировать и закодировать. (обязательно для -a)")
    parser.add_argument("resultimage", nargs="?", type=str, help="Имя или путь+имя файла, в который запишется картинка с помехоустойчиво закодированным архивом. (обязательно для -a)")
    
    parser.add_argument("-x", action="store_true", help="Нужен режим раскодирования и разархивирования")
    parser.add_argument("image", nargs="?", type=str, help="Имя файла-картинки с помехоустойчиво закодированным архивом. (обязательно для -x)")
    parser.add_argument("resultpath", nargs="?", type=str, help="Путь до папки, в которую записать полученные из архива файлы. Если не указан, архив распаковывается в текущую папку. (необязательно для -x)")

    args = vars(parser.parse_args())
    
    if args["a"] == args["x"]:
        parser.exit(parser.print_help())
    if args["x"] and args["image"] != None:
        parser.exit(parser.print_help())
    if args["x"]:
        args["image"] = args["path"]
        args["resultpath"] = args["resultimage"]
    if args["a"] and (args["path"] == None or args["resultimage"] == None):
        parser.exit(parser.print_help())
    if args["x"] and args["image"] == None:
        parser.exit(parser.print_help())

    return args

def packing(path):
    from shutil import make_archive
    
    return make_archive(path, "zip", path)

def coding(archive_name):
    data = open(archive_name, "rb").read()
    bin_code = []
    
    for i in range(len(data)):
        byte = "%s" % (bin(data[i])[2:].zfill(8))
        r_bits_1 = get_r_bits(byte[0:4])
        r_bits_2 = get_r_bits(byte[4:8])
        bin_code.append("%s%s" % (byte[0:4], r_bits_1))
        bin_code.append("%s%s" % (byte[4:8], r_bits_2))
    
    return bin_code

def get_r_bits(d_bits):
    return ''.join([
          str(int(d_bits[0]) ^ int(d_bits[1]) ^ int(d_bits[2])),
          str(int(d_bits[1]) ^ int(d_bits[2]) ^ int(d_bits[3])),
          str(int(d_bits[0]) ^ int(d_bits[1]) ^ int(d_bits[3])),
    ])

def making_bmp(bin_code, resultimage):
    from math import ceil, sqrt
    from struct import Struct
    from sys import exit
    
    dpi_h, dpi_v = 150, 150
    side = ceil(sqrt(len(bin_code) / 10))
    pixels = (side + 2) ** 2 * 70
    maximum = dpi_h * dpi_v * 8 * 11
    if maximum < pixels:
        print("Too big file. %d pixels. Maximum %d pixels. %d dpi" % (pixels, maximum, dpi_h))
        exit()
    
    for i in range((side ** 2) - len(bin_code) % (side ** 2)):
        bin_code.append('0000000')
    while len(bin_code) / (side ** 2) < 10:
        for i in range(side ** 2):
            bin_code.append('0000000')
    blocks = blocking_to_bmp(bin_code, side)
    f = open(resultimage, "wb")
    byte_0 = bytes([int('1' * 8, 2)] * 3)
    byte_1 = bytes([int('0' * 8, 2)] * 3)    
    content = b''
    line = []
    for i in range(10 * (side + 2)):
        pos = int(i / (side + 2))
        line.append(blocks[pos][i % (side + 2)])
        for k in range(1, 7):
            line[i] = ''.join([line[i], blocks[10 * k +(pos + (10 - 3 * k) % 10) % 10][i % (side + 2)]])
    content = bytes([])
    ost = bytes([int('0', 2)] * (len(line[0]) % 4))
    i = -1
    
    while i >= -len(line):
        for j in range(len(line[i])):
            if line[i][j] == '1':
                content += byte_1 
            else:
                content += byte_0  
        content += ost
        i -= 1
    size = len(content)
    width = 7 * (side + 2)
    height = 10 * (side + 2)
    PPM_h, PPM_v = int(39.3700787 * dpi_h), int(39.3700787 * dpi_v)
    header_struct = Struct("<   2s                   I   4x   I       I      I       I        H       H    I       I        I     I       I       I")
    header = header_struct.pack('BM'.encode(), size + 54,     54,     40, width,    height,   1,      24,  0,    size,  PPM_h, PPM_v,     0,      0)
    f.write(header)
    f.write(content)
    f.close()

def blocking_to_bmp(bin_code, side):
    blocks = [[]]
    border = '01'
    k = 0
    for x in range(7):
        number_of_lines = 0
        for y in range(10):
            blocks.append([])
            blocks[k].append(border[1] * (side + 2))
            for j in range(side):
                line = "".join([border[j % 2], data_line(bin_code, side, number_of_lines, x), border[1]])
                blocks[k].append(line)
                number_of_lines += 1
            blocks[k].append(border[1] * (side % 2) + border * int(side / 2 + 1))
            k += 1
    return blocks[:-1]

def data_line(bin_code, side, k, bit):
    line = ''
    for i in range(k * side, (k + 1) * side):
        line = "".join([line, bin_code[i][bit]])
    return line

def decoding_image(image_name):
    from itertools import count
    
    bin_code = ''
    content = open(image_name, "rb").read()
    wid = [content[18], content[19], content[20], content[21]]
    hei = [content[22], content[23], content[24], content[25]]
    wid = 256 * wid[3] + 256 * wid[2] + 256 * wid[1] + wid[0]
    hei = 256 * hei[3] + 256 * hei[2] + 256 * hei[1] + hei[0]
    if (wid * 3) % 4 != 0:
        lenght = wid * 3 + 4 - (wid * 3) % 4
    else:
        lenght = wid * 3
    data = content[54:]
    i = hei-1

    while i > -1:
        line = data[lenght * (i):lenght * (i + 1)]
        line = line[:wid * 3]
        for j in count(0, 3):
            if line[j] == 0:
                bin_code = ''.join([bin_code, "1"])
            else:
                bin_code = ''.join([bin_code, "0"])
            if j > wid * 3 - 6:
                break
        i -= 1
    return blocking_from_bmp(bin_code, wid)

def blocking_from_bmp(bin_code, wid):
    blocks = ['']
    side = int(wid / 7)
    k = 0
    for x in range(1, 8):
        for y in range(1, 11):
            for i in range(1, side-1):
                start = side * (x - 1) + wid * i + wid * side * (y - 1) + 1
                finish = side * x + wid * i + wid * side * (y - 1) - 1
                blocks[k] = "".join([blocks[k], bin_code[start:finish]])
        k += 1
        blocks.append('')
    for i in range(1, 7):
        blocks[i] = ''.join([
                            blocks[i][(i * 3) % 10 * (side - 2) * (side - 2):],
                            blocks[i][:(i * 3) % 10 * (side - 2) * (side - 2)]
                            ])

    return blocks[:-1]

def restoring_archive(blocks):
    byte_code = []
    k = 0
    archive_name = "temp.zip"
    while k < len(blocks[0]):
        byte = ''
        for i in range(2):
            bits = ''            
            for j in range(len(blocks)):
                bits = "".join([bits, blocks[j][k+i]])
            byte = "".join([byte, restoring_bits(bits)])
        byte_code.append(int(byte, 2))
        k += 2
    open(archive_name, "wb").write(bytes(byte_code))
    return archive_name

def restoring_bits(bits):
    from  functools import reduce
    
    bits = list(bits)
    sindrom = {
        '000':-1,
        '101':0,
        '111':1,
        '110':2,
        '011':3,
        '100':4,
        '010':5,
        '001':6,
    }
    matrix = (
       (1, 0, 1),
       (1, 1, 1),
       (1, 1, 0),
       (0, 1, 1),
       (1, 0, 0),
       (0, 1, 0),
       (0, 0, 1),
    )
    s = [map(lambda x, y: int(x) * int(y), [matrix[j][i] for j in range(7)], bits) for i in range(3)]
    s = [reduce(lambda x, y: x ^ y, i) for i in s]
    for i in range(len(s)):
        s[i] = str(s[i])
    s = ''.join(s)
    bits = ''.join(bits)
    if sindrom[s] != -1:
        if bits[sindrom[s]] == '0':
            bits = ''.join([bits[:sindrom[s]], '1', bits[sindrom[s]+1:]])
        else:
            bits = ''.join([bits[:sindrom[s]], '0', bits[sindrom[s]+1:]])
    return bits[:4]

def unpacking(archive_name, resultpath):
    from shutil import unpack_archive
    if resultpath != None:
        unpack_archive(archive_name, resultpath)
    else:
        unpack_archive(archive_name, 'result')

if __name__ == "__main__":
    main()