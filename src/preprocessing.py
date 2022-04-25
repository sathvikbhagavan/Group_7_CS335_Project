import re
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-n", "--num", type=int, required=True, help="test case number")
args = vars(ap.parse_args())

f = open(f"tests/test_{args['num']}.cpp", "r")
lines = f.read().splitlines()
n = len(lines)
txt2 = ""
dict = {}
lis = []
for l in lines:
    if l.find("typedef") == -1:
        txt2 = txt2 + l + "\n"
        continue
    l2 = re.split("\s+|;", l)
    i = l2.index("typedef")
    lis.append(l2[i + 2])
    dict[l2[i + 2]] = l2[i + 1]

delis = [";", ")", "(", ":", ","]
txt1 = txt2
txt2 = ""
for b in lis:
    h = len(b)
    lns = txt1.splitlines()
    for l in lns:
        x = l.split()
        k1 = 0
        k2 = 0

        for i in x:
            gg = i.find(b)
            if gg == -1:
                txt2 = txt2 + i + " "
                continue
            if gg != 0:
                if i[gg - 1] not in delis:
                    txt2 = txt2 + i + " "
                    continue
            if gg < len(i) - len(b):
                if i[gg + len(b)] not in delis:
                    txt2 = txt2 + i + " "
                    continue
            i = i.replace(b, dict[b])
            txt2 = txt2 + i + " "
        txt2 = txt2 + "\n"
    txt1 = txt2
    txt2 = ""


f1 = open(f"tests/test_{args['num']}_processed.cpp", "w")
f1.write(txt1)
f1.close()
f.close()

f = open(f"tests/test_{args['num']}_processed.cpp", "r+")
lines = f.read().splitlines()
n = len(lines)
j = 0
txt = ""
while j < n:
    l = lines[j]

    k = l.find("#include")
    k3 = l.find('"')
    k4 = l.find('"', k3 + 1)

    if k == -1:
        txt += l + "\n"
        j += 1
        continue
    if l.find("#include", k + 1) != -1:
        j += 1
        print('Error: more than one "#include" in one line')
        continue
    if k > k3 and k < k4:
        txt += l + "\n"
        j += 1
        continue
    k1 = l.find("<")
    k2 = l.find(">")
    if k1 == -1 or k2 == -1:
        print("Syntax Error in \#include")
    j += 1
    myhdr = l[k1 + 1 : k2]
    try:
        fil = open(myhdr, "r")
    except:
        print("myhdr file doesn't exist")
        continue
    corpus = fil.read()
    txt += corpus

f1 = open(f"tests/test_{args['num']}_processed.cpp", "w")
f1.write(txt)
f1.close()
f.close()
