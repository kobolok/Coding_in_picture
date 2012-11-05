# -*- coding: utf-8 -*- 

from itertools import count

text = ''
bin_code = ''
content = open("message.bmp", "rb").read()
wid = content[18]
hei = content[22]
lenght = wid * 3 + 4 - (wid * 3) % 4
data = content[54:-lenght]
i = hei-2

while i > 0:    
    line = data[lenght * (i):lenght * (i + 1)]
    line = line[3:wid * 3 - 3]
    for j in count(0, 3):
        if line[j] == 0:
            bin_code = ''.join([bin_code, "1"])
        else:
            bin_code = ''.join([bin_code, "0"])
        if j > wid * 3 - 10:
            break
    i -= 1

i = 0
sym = ''

while i < len(bin_code) - 1:
    bit = bin_code.find("0",i) - i
    if bit == 0:        
        sym_code = bin_code[i+1:i+8]
        sym = chr(int(sym_code, 2))
        i += 8
    elif bit == 2:
        sym_code = bin_code[i+3:i+8] + bin_code[i+10:i+16]
        sym = chr(int(sym_code, 2))
        i += 16
    elif bit == 3:
        sym_code = bin_code[i+4:i+8] + bin_code[i+10:i+16] + bin_code[i+18:i+24]
        sym = chr(int(sym_code, 2))
        i += 24
    elif bit == 4:
        sym_code = bin_code[i+5:i+8] + bin_code[i+10:i+16] + bin_code[i+18:i+24] + bin_code[i+26:i+32]
        sym = chr(int(sym_code, 2))
        i += 32
    elif bit == 5:
        sym_code = bin_code[i+6:i+8] + bin_code[i+10:i+16] + bin_code[i+18:i+24] + bin_code[i+26:i+32] + bin_code[i+34:i+40]
        sym = chr(int(sym_code, 2))
        i += 40
    text = ''.join([text, sym])

open("out.txt","w", encoding="UTF-8").write(text);