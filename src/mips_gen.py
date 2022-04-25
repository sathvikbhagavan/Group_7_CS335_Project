import pickle
import re
import operator
import struct
import struct

lineno = 0
func_par = {}
func_var = {}
offset, param_offset = {}, {}
curr_function = ""
func_type = {}
is_return = 0
with open("bin/3AC.code") as f:
    lines = f.read().splitlines()
    n = len(lines)
    j = 0
    while j < n:
        i = lines[j]
        lineno = lineno + 1
        string = i.split(" ")
        if i.find("Func_Start") == -1:
            j += 1
            continue
        else:
            i = lines[j - 1]
            string = lines[j - 1].split(" ")
            func_name = string[0]
            func_par[func_name] = []
            func_var[func_name] = []

            for k in string:
                if k[:3] == "reg":
                    func_par[func_name].append(k)

            j += 1
            while j < n and lines[j].find("Func_End") == -1:
                string = lines[j].split(" ")
                for k in string:
                    if (
                        k[:3] == "reg"
                        and k not in func_var[func_name]
                        and k not in func_par[func_name]
                    ):
                        func_var[func_name].append(k)
                j += 1

# print("func_var", func_var)
# print("func_par",func_par)



### bitwise opertor and modulus both operands should be int
dtype_size = {"int": 4, "float": 4, "char": 4}
jump_ctr = 0
arith_op = {"+": "add", "*": "mul", "-": "sub", "/": "div"}
bitwise_op = {"|": "or", "&": "and", "^": "xor", "<<": "sll", ">>": "srl"}
integer_cond_op = {
    ">=": "bge",
    "<=": "ble",
    "==": "beq",
    "!=": "bne",
    "<": "blt",
    ">": "bgt",
}
###greater than and not equals does not work in float (workaround implemented)
float_cond_op = {
    ">=": "c.le.s",
    "<=": "c.le.s",
    "==": "c.eq.s",
    "!=": "c.eq.s",
    "<": "c.lt.s",
    ">": "c.lt.s",
}


def float_to_hex(f):
    return hex(struct.unpack("<I", struct.pack("<f", f))[0])


file = open("src/register_type.obj", "rb")
register_type = pickle.load(file)
code = ["    .data"]
code.append('Exit:    .asciiz "[Runtime Error] Assertion Error"')
lineno = 0
space = ["    "]

# for i in register_type.keys():
#     print(i,register_type[i])

with open("src/activation_record.txt", "w") as f:
    for i in func_var.keys():
        f.write(f"Function: {i}\n")
        f.write(f"Parameters: {func_par[i]}\n")
        f.write(f"Variables: {func_var[i]}\n")
    for i in register_type.keys():
        f.write(f"Register: {' '.join(map(str, register_type[i]))}\n")


def save_memb_var_on_stack(caller, called):
    global code, offset, func_var, func_var
    # print("caller = ",caller,"  callee = ",called)
    total_size = 0
    saving_lines = []
    for i in func_var[caller]:

        if register_type[i][0] == "reg_array":
            offset[i] = total_size
            saving_lines.append(space + space + ["la $t1, " + i])
            for size in range(0, register_type[i][2], dtype_size[register_type[i][1]]):
                reg_size = dtype_size[register_type[i][1]]
                total_size += reg_size
                if register_type[i][1] == "float":
                    saving_lines.append(space + space + ["lwc1 $f1, 0($t1)"])
                    saving_lines.append(
                        space + space + ["swc1 $f1, " + str(total_size) + "($sp)"]
                    )
                    saving_lines.append(
                        space
                        + space
                        + ["addi $t1, $t1 " + str(dtype_size[register_type[i][1]])]
                    )
                else:
                    saving_lines.append(space + space + ["lw $t2, 0($t1)"])
                    saving_lines.append(
                        space + space + ["sw $t2, " + str(total_size) + "($sp)"]
                    )
                    saving_lines.append(
                        space
                        + space
                        + ["addi $t1, $t1 " + str(dtype_size[register_type[i][1]])]
                    )
            pass
        else:
            reg_size = dtype_size[register_type[i][1]]
            total_size += reg_size
            offset[i] = total_size  ####maintain offset for array
            if register_type[i][1] == "float":
                saving_lines.append(space + space + ["lwc1 $f1, " + i])
                saving_lines.append(
                    space + space + ["swc1 $f1, " + str(total_size) + "($sp)"]
                )
            else:
                saving_lines.append(space + space + ["lw $t1, " + i])
                saving_lines.append(
                    space + space + ["sw $t1, " + str(total_size) + "($sp)"]
                )

    for i in func_par[caller]:
        reg_size = dtype_size[register_type[i][1]]
        total_size += reg_size
        if register_type[i][0] == "reg_array":
            ###need to do #####
            ### no array in parameters ###
            pass
        else:
            offset[i] = total_size
            if register_type[i][1] == "float":
                saving_lines.append(space + space + ["lwc1 $f1, " + i])
                saving_lines.append(
                    space + space + ["swc1 $f1, " + str(total_size) + "($sp)"]
                )
            else:
                saving_lines.append(space + space + ["lw $t1, " + i])
                saving_lines.append(
                    space + space + ["sw $t1, " + str(total_size) + "($sp)"]
                )

    code = code + [space + space + ["add $sp -" + str(total_size)]] + saving_lines


def save_memb_var_back_to_memory(caller, called):
    global code, offset
    # print("caller = ",caller,"  callee = ",called)
    total_size = 0
    for i in offset.keys():
        if i in func_var[caller] or i in func_par[caller]:

            if register_type[i][0] == "reg_array":
                reg_size = dtype_size[register_type[i][1]] * register_type[i][2]
                total_size += reg_size
                arr_offset = offset[i]
                code.append(space + space + ["la $t1, " + i])
                for size in range(
                    0, register_type[i][2], dtype_size[register_type[i][1]]
                ):

                    if register_type[i][1] == "float":
                        code.append(
                            space + space + ["lwc1 $f1, " + str(arr_offset) + "($sp)"]
                        )
                        code.append(space + space + ["swc1 $f1, 0($t1)"])
                        code.append(
                            space
                            + space
                            + ["addi $t1, $t1 " + str(dtype_size[register_type[i][1]])]
                        )
                    else:
                        code.append(
                            space + space + ["lw $t2, " + str(arr_offset) + "($sp)"]
                        )
                        code.append(space + space + ["sw $t2, 0($t1)"])
                        code.append(
                            space
                            + space
                            + ["addi $t1, $t1 " + str(dtype_size[register_type[i][1]])]
                        )

                    arr_offset += dtype_size[register_type[i][1]]
                ###need to do #####
                pass
            else:
                reg_size = dtype_size[register_type[i][1]]
                total_size += reg_size
                if register_type[i][1] == "float":
                    code.append(
                        space + space + ["lwc1 $f1, " + str(offset[i]) + "($sp)"]
                    )
                    code.append(space + space + ["swc1 $f1, " + i])
                else:
                    code.append(space + space + ["lw $t1, " + str(offset[i]) + "($sp)"])
                    code.append(space + space + ["sw $t1, " + i])

    code.append(space + space + ["add $sp, " + str(total_size)])


def put_parameters_on_memory(func):
    global code, param_offset, func_par
    saving_lines = []
    total_size = 0
    for param in func_par[func]:
        reg_size = dtype_size[register_type[param][1]]
        total_size += reg_size
        if register_type[param][0] == "reg_array":
            ###need to do #####
            pass
        else:
            if register_type[param][1] == "float":
                code.append(
                    space + space + ["lwc1 $f1, " + str(param_offset[param]) + "($sp)"]
                )
                code.append(space + space + ["swc1 $f1, " + param])
            else:
                code.append(
                    space + space + ["lw $t1, " + str(param_offset[param]) + "($sp)"]
                )
                code.append(space + space + ["sw $t1, " + param])

    code.append(space + space + ["add $sp, " + str(total_size)])


def put_parameters_on_stack(caller, called, param_list):
    global code, func_par
    saving_lines = []
    total_size = 0
    itr = -1
    for actual_param in param_list:
        itr = itr + 1
        reg_size = dtype_size[register_type[actual_param][1]]
        total_size += reg_size
        formal_param = func_par[called][itr]
        if register_type[actual_param][0] == "reg_array":
            pass
        else:
            if register_type[formal_param][1] == "float":
                if register_type[actual_param][1] == "float":
                    saving_lines.append(space + space + ["lwc1 $f1, " + actual_param])
                    saving_lines.append(
                        space + space + ["swc1 $f1, " + str(total_size) + "($sp)"]
                    )
                else:
                    saving_lines.append(space + space + ["lw $t1, " + actual_param])
                    saving_lines.append(space + space + ["mtc1 $t1, $f1"])
                    saving_lines.append(space + space + ["cvt.s.w $f1,$f1"])
                    saving_lines.append(
                        space + space + ["swc1 $f1, " + str(total_size) + "($sp)"]
                    )
            else:
                if register_type[actual_param][1] == "float":
                    saving_lines.append(space + space + ["lwc1 $f20, " + actual_param])
                    saving_lines.append(space + space + ["cvt.w.s $f1, $f20"])
                    saving_lines.append(space + space + ["mfc1 $t1, $f1"])
                    saving_lines.append(
                        space + space + ["sw $t1, " + str(total_size) + "($sp)"]
                    )
                else:
                    saving_lines.append(space + space + ["lw $t1, " + actual_param])
                    saving_lines.append(
                        space + space + ["sw $t1, " + str(total_size) + "($sp)"]
                    )

    code = code + [space + space + ["add $sp -" + str(total_size)]] + saving_lines


def instr_classifier(instr, arg):
    global func_type, curr_function, code, param_offset, offset, func_par, func_var, is_return
    if instr in arith_op.keys():

        opr = arith_op[instr]
        code.append(space + space + ["la $t1, " + arg[1]])
        code.append(space + space + ["la $t2, " + arg[2]])
        code.append(space + space + ["la $t3, " + arg[0]])

        if register_type[arg[1]][1] == "float" or register_type[arg[2]][1] == "float":
            if (
                register_type[arg[1]][1] == "float"
                and register_type[arg[2]][1] == "float"
            ):
                code.append(space + space + ["lwc1 $f20,0($t1)"])
                code.append(space + space + ["lwc1 $f21,0($t2)"])
                code.append(space + space + [opr + ".s $f20, $f20, $f21"])
                if register_type[arg[0]][1] == "float":
                    code.append(space + space + ["swc1 $f20,0($t3)"])
                else:
                    code.append(space + space + ["cvt.w.s $f1, $f20"])
                    code.append(space + space + ["mfc1 $t4, $f1"])
                    code.append(space + space + ["sw $t4,0($t3)"])
            elif register_type[arg[1]][1] != "float":
                code.append(space + space + ["lw $t4,0($t1)"])
                code.append(space + space + ["mtc1 $t4,$f20"])
                code.append(space + space + ["cvt.s.w $f20, $f20"])
                code.append(space + space + ["lwc1 $f21,0($t2)"])
                code.append(space + space + [opr + ".s $f20, $f20, $f21"])
                if register_type[arg[0]][1] == "float":
                    code.append(space + space + ["swc1 $f20,0($t3)"])
                else:
                    code.append(space + space + ["cvt.w.s $f1, $f20"])
                    code.append(space + space + ["mfc1 $t4, $f1"])
                    code.append(space + space + ["sw $t4,0($t3)"])
            elif register_type[arg[2]][1] != "float":
                code.append(space + space + ["lw $t4,0($t2)"])
                code.append(space + space + ["mtc1 $t4,$f21"])
                code.append(space + space + ["cvt.s.w $f21, $f21"])
                code.append(space + space + ["lwc1 $f20,0($t1)"])
                code.append(space + space + [opr + ".s $f20, $f20, $f21"])
                if register_type[arg[0]][1] == "float":
                    code.append(space + space + ["swc1 $f20,0($t3)"])
                else:
                    code.append(space + space + ["cvt.w.s $f1, $f20"])
                    code.append(space + space + ["mfc1 $t4, $f1"])
                    code.append(space + space + ["sw $t4,0($t3)"])
        else:
            code.append(space + space + ["lw $t4,0($t1)"])
            code.append(space + space + ["lw $t5,0($t2)"])
            code.append(space + space + [opr + " $t4, $t4, $t5"])
            if register_type[arg[0]][1] == "float":
                code.append(space + space + ["mtc1 $t4, $f1"])
                code.append(space + space + ["cvt.s.w $f1,$f1"])
                code.append(space + space + ["swc1 $f1,0($t3)"])
            else:
                code.append(space + space + ["sw $t4,0($t3)"])

    if instr in bitwise_op.keys():

        opr = bitwise_op[instr]
        code.append(space + space + ["lw $t1, " + arg[1]])
        code.append(space + space + ["lw $t2, " + arg[2]])
        code.append(space + space + ["la $t3, " + arg[0]])
        code.append(space + space + [opr + " $t1, $t1, $t2"])
        if register_type[arg[1]][1] == "float":
            code.append(space + space + ["mtc1 $t1, $f1"])
            code.append(space + space + ["cvt.s.w $f1,$f1"])
            code.append(space + space + ["swc1 $f1,0($t3)"])
        else:
            code.append(space + space + ["sw $t1, 0($t3)"])

    if instr in integer_cond_op.keys():
        global jump_ctr
        code.append(space + space + ["la $t1, " + arg[1]])
        code.append(space + space + ["la $t2, " + arg[2]])
        code.append(space + space + ["la $t3, " + arg[0]])

        if register_type[arg[1]][1] == "float" or register_type[arg[2]][1] == "float":
            opr = float_cond_op[instr]
            if (
                register_type[arg[1]][1] == "float"
                and register_type[arg[2]][1] == "float"
            ):

                if register_type[arg[0]][1] == "float":
                    if instr[0] == "!":
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(0))]
                        )
                    else:
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(1))]
                        )
                    code.append(space + space + ["mtc1 $t6, $f1"])
                    code.append(space + space + ["cvt.s.w $f1,$f1"])
                    code.append(space + space + ["lwc1 $f20,0($t1)"])
                    code.append(space + space + ["lwc1 $f21,0($t2)"])
                    if instr[0] == "<":
                        code.append(space + space + [opr + " $f20, $f21"])
                    else:
                        code.append(space + space + [opr + " $f21, $f20"])
                    code.append(space + space + [f"bc1t jump{jump_ctr}"])
                    if instr[0] == "!":
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(1))]
                        )
                    else:
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(0))]
                        )
                    code.append(space + space + ["mtc1 $t6, $f1"])
                    code.append([f"jump{jump_ctr}:"])
                    code.append(space + space + ["swc1 $f1,0($t3)"])
                    jump_ctr += 1

                else:
                    if instr[0] == "!":
                        code.append(space + space + ["addi $t6, $0, 0"])
                    else:
                        code.append(space + space + ["addi $t6, $0, 1"])
                    code.append(space + space + ["lwc1 $f20,0($t1)"])
                    code.append(space + space + ["lwc1 $f21,0($t2)"])
                    if instr[0] == "<":
                        code.append(space + space + [opr + " $f20, $f21"])
                    else:
                        code.append(space + space + [opr + " $f21, $f20"])
                    code.append(space + space + [f"bc1t jump{jump_ctr}"])
                    if instr[0] == "!":
                        code.append(space + space + ["addi $t6, $0, 1"])
                    else:
                        code.append(space + space + ["addi $t6, $0, 0"])
                    code.append([f"jump{jump_ctr}:"])
                    code.append(space + space + ["sw $t6,0($t3)"])
                    jump_ctr += 1

            elif register_type[arg[1]][1] != "float":
                if register_type[arg[0]][1] == "float":

                    if instr[0] == "!":
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(0))]
                        )
                    else:
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(1))]
                        )
                    code.append(space + space + ["mtc1 $t6, $f1"])
                    code.append(space + space + ["cvt.s.w $f1,$f1"])
                    code.append(space + space + ["lw $t4,0($t1)"])
                    code.append(space + space + ["mtc1 $t4,$f20"])
                    code.append(space + space + ["cvt.s.w $f20, $f20"])
                    code.append(space + space + ["lwc1 $f21,0($t2)"])
                    if instr[0] == "<":
                        code.append(space + space + [opr + " $f20, $f21"])
                    else:
                        code.append(space + space + [opr + " $f21, $f20"])
                    code.append(space + space + [f"bc1t jump{jump_ctr}"])
                    if instr[0] == "!":
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(1))]
                        )
                    else:
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(0))]
                        )
                    code.append(space + space + ["mtc1 $t6, $f1"])
                    code.append([f"jump{jump_ctr}:"])
                    code.append(space + space + ["swc1 $f1,0($t3)"])
                    jump_ctr += 1
                else:
                    if instr[0] == "!":
                        code.append(space + space + ["addi $t6, $0, 0"])
                    else:
                        code.append(space + space + ["addi $t6, $0, 1"])
                    code.append(space + space + ["lw $t4,0($t1)"])
                    code.append(space + space + ["mtc1 $t4,$f20"])
                    code.append(space + space + ["cvt.s.w $f20, $f20"])
                    code.append(space + space + ["lwc1 $f21,0($t2)"])
                    if instr[0] == "<":
                        code.append(space + space + [opr + " $f20, $f21"])
                    else:
                        code.append(space + space + [opr + " $f21, $f20"])
                    code.append(space + space + [f"bc1t jump{jump_ctr}"])
                    if instr[0] == "!":
                        code.append(space + space + ["addi $t6, $0, 1"])
                    else:
                        code.append(space + space + ["addi $t6, $0, 0"])
                    code.append([f"jump{jump_ctr}:"])
                    code.append(space + space + ["sw $t6,0($t3)"])
                    jump_ctr += 1

            elif register_type[arg[2]][1] != "float":
                if register_type[arg[0]][1] == "float":

                    if instr[0] == "!":
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(0))]
                        )
                    else:
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(1))]
                        )
                    code.append(space + space + ["mtc1 $t6, $f1"])
                    code.append(space + space + ["cvt.s.w $f1,$f1"])
                    code.append(space + space + ["lwc1 $f20,0($t1)"])
                    code.append(space + space + ["lw $t4,0($t2)"])
                    code.append(space + space + ["mtc1 $t4,$f21"])
                    code.append(space + space + ["cvt.s.w $f21, $f21"])
                    if instr[0] == "<":
                        code.append(space + space + [opr + " $f20, $f21"])
                    else:
                        code.append(space + space + [opr + " $f21, $f20"])
                    code.append(space + space + [f"bc1t jump{jump_ctr}"])
                    if instr[0] == "!":
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(1))]
                        )
                    else:
                        code.append(
                            space + space + ["li $t6, "] + [str(float_to_hex(0))]
                        )
                    code.append(space + space + ["mtc1 $t6, $f1"])

                    code.append([f"jump{jump_ctr}:"])
                    code.append(space + space + ["swc1 $f1,0($t3)"])
                    jump_ctr += 1

                else:
                    if instr[0] == "!":
                        code.append(space + space + ["addi $t6, $0, 0"])
                    else:
                        code.append(space + space + ["addi $t6, $0, 1"])
                    code.append(space + space + ["lwc1 $f20,0($t1)"])
                    code.append(space + space + ["lw $t4,0($t2)"])
                    code.append(space + space + ["mtc1 $t4,$f21"])
                    code.append(space + space + ["cvt.s.w $f21, $f21"])
                    if instr[0] == "<":
                        code.append(space + space + [opr + " $f20, $f21"])
                    else:
                        code.append(space + space + [opr + " $f21, $f20"])
                    code.append(space + space + [f"bc1t jump{jump_ctr}"])
                    if instr[0] == "!":
                        code.append(space + space + ["addi $t6, $0, 1"])
                    else:
                        code.append(space + space + ["addi $t6, $0, 0"])
                    code.append([f"jump{jump_ctr}:"])
                    code.append(space + space + ["sw $t6,0($t3)"])
                    jump_ctr += 1

        else:
            opr = integer_cond_op[instr]
            if register_type[arg[0]][1] == "float":
                code.append(space + space + ["li $t6, "] + [str(float_to_hex(1))])
                code.append(space + space + ["mtc1 $t6, $f1"])
                code.append(space + space + ["cvt.s.w $f1,$f1"])
                code.append(space + space + ["lw $t4,0($t1)"])
                code.append(space + space + ["lw $t5,0($t2)"])
                code.append(space + space + [opr + f" $t4, $t5, jump{jump_ctr}"])
                code.append(space + space + ["li $t6, "] + [str(float_to_hex(0))])
                code.append(space + space + ["mtc1 $t6, $f1"])
                code.append([f"jump{jump_ctr}:"])
                code.append(space + space + ["swc1 $f1,0($t3)"])
                jump_ctr += 1
            else:
                code.append(space + space + ["addi $t6, $0, 1"])
                code.append(space + space + ["lw $t4,0($t1)"])
                code.append(space + space + ["lw $t5,0($t2)"])
                code.append(space + space + [opr + f" $t4, $t5, jump{jump_ctr}"])
                code.append(space + space + ["addi $t6, $0, 0"])
                code.append([f"jump{jump_ctr}:"])
                code.append(space + space + ["sw $t6,0($t3)"])
                jump_ctr += 1

    if instr == "||" or instr == "&&":
        opr = "and"
        if instr == "||":
            opr = "or"

        code.append(space + space + ["la $t1, " + arg[1]])
        code.append(space + space + ["la $t2, " + arg[2]])
        code.append(space + space + ["la $t3, " + arg[0]])

        if register_type[arg[0]][1] == "float":
            code.append(space + space + ["li $t6, "] + [str(float_to_hex(1))])
            code.append(space + space + ["mtc1 $t6, $f1"])
            code.append(space + space + ["cvt.s.w $f1,$f1"])
            code.append(space + space + ["lw $t4,0($t1)"])
            code.append(space + space + ["lw $t5,0($t2)"])
            code.append(space + space + [opr + " $t7, $t4, $t5"])
            code.append(space + space + [f"bne $t7, $0, jump{jump_ctr}"])
            code.append(space + space + ["li $t6, "] + [str(float_to_hex(0))])
            code.append(space + space + ["mtc1 $t6, $f1"])
            code.append([f"jump{jump_ctr}:"])
            code.append(space + space + ["swc1 $f1,0($t3)"])
            jump_ctr += 1
        else:
            code.append(space + space + ["addi $t6, $0, 1"])
            code.append(space + space + ["lw $t4,0($t1)"])
            code.append(space + space + ["lw $t5,0($t2)"])
            code.append(space + space + [opr + " $t7, $t4, $t5"])
            code.append(space + space + [f"bne $t7, $0, jump{jump_ctr}"])
            code.append(space + space + ["addi $t6, $0, 0"])
            code.append([f"jump{jump_ctr}:"])
            code.append(space + space + ["sw $t6,0($t3)"])
            jump_ctr += 1

    if instr == "%":
        code.append(space + space + ["la $t3, " + arg[0]])
        code.append(space + space + ["lw $t1, " + arg[1]])
        code.append(space + space + ["lw $t2, " + arg[2]])
        code.append(space + space + ["div $t1, $t2"])
        code.append(space + space + ["mfhi $t4"])
        code.append(space + space + ["sw $t4, 0($t3)"])
    if instr[:9] == "outputstr":
        code.append(space + space + ["li $v0, 4"])
        code.append(space + space + ["la $a0, "] + [instr])
        code.append(space + space + ["syscall"])
        pass
    if instr == "outputvar":
        code.append(space + space + ["la $t1, " + arg[0]])

        if register_type[arg[0]][1] == "float":
            code.append(space + space + ["lwc1 $f1,0($t1)"])
            code.append(space + space + ["li $v0, 2"])
            code.append(space + space + ["mov.s $f12,$f1"])
            code.append(space + space + ["syscall"])

        elif register_type[arg[0]][1] == "int":
            code.append(space + space + ["lw $a0,0($t1)"])
            code.append(space + space + ["li $v0, 1"])
            code.append(space + space + ["syscall"])

        elif register_type[arg[0]][1] == "char":
            code.append(space + space + ["lw $a0,0($t1)"])
            code.append(space + space + ["li $v0, 11"])
            code.append(space + space + ["syscall"])

    if instr == "input":
        code.append(space + space + ["la $t1, " + arg[0]])

        if register_type[arg[0]][1] == "float":
            code.append(space + space + ["li $v0, 6"])
            code.append(space + space + ["syscall"])
            code.append(space + space + ["swc1 $f0,0($t1)"])

        elif register_type[arg[0]][1] == "int":
            code.append(space + space + ["li $v0, 5"])
            code.append(space + space + ["syscall"])
            code.append(space + space + ["sw $v0,0($t1)"])

        elif register_type[arg[0]][1] == "char":
            code.append(space + space + ["li $v0, 12"])
            code.append(space + space + ["syscall"])
            code.append(space + space + ["sw $v0,0($t1)"])

    if instr == "assignment_expression":
        code.append(space + space + ["la $t1, " + arg[0]])
        code.append(space + space + ["la $t2, " + arg[1]])
        if register_type[arg[0]][1] == "float":
            if register_type[arg[1]][1] == "float":
                code.append(space + space + ["lwc1 $f1, 0($t2)"])
                code.append(space + space + ["swc1 $f1, 0($t1)"])
            else:
                code.append(space + space + ["lw $t3, 0($t2)"])
                code.append(space + space + ["mtc1 $t3, $f1"])
                code.append(space + space + ["cvt.s.w $f1,$f1"])
                code.append(space + space + ["swc1 $f1, 0($t1)"])

        elif register_type[arg[0]][1] != "float":
            if register_type[arg[1]][1] == "float":
                code.append(space + space + ["lwc1 $f1, 0($t2)"])
                code.append(space + space + ["cvt.w.s $f2, $f1"])
                code.append(space + space + ["mfc1 $t3, $f2"])
                code.append(space + space + ["sw $t3, 0($t1)"])
            else:
                code.append(space + space + ["lw $t3, 0($t2)"])
                code.append(space + space + ["sw $t3, 0($t1)"])
    if instr == "Function_Label:":
        is_return = 0
        code.append([arg[0] + ":"])
        curr_function = arg[0]
        func_type[arg[0]] = arg[1]
        if arg[0] != "main":
            total_size = 0
            for param in func_par[curr_function]:
                reg_size = dtype_size[register_type[param][1]]
                total_size += reg_size
                param_offset[param] = total_size
            # put parameters in memory and sp management
            put_parameters_on_memory(curr_function)
            # save return address
            code.append(space + space + ["sw $ra, ($sp)"])
            code.append(space + space + ["add $sp, -4"])
        pass
    if instr == "constant_assignment":
        code.append(space + space + ["la $t1, " + arg[0]])
        if register_type[arg[0]][1] == "float":
            code.append(
                space + space + ["li $t2, "] + [str(float_to_hex(float(arg[1])))]
            )
            code.append(space + space + ["mtc1 $t2, $f1"])
            code.append(space + space + ["swc1 $f1,0($t1)"])
        else:
            code.append(space + space + ["addi $t2, $0, "] + [str(int(arg[1]))])
            code.append(space + space + ["sw $t2, 0($t1)"])
    if instr == "goto":
        pass
    if instr == "ifgoto":
        code.append(space + space + ["j " + arg[0]])
    if instr == "Label":
        code.append([arg[0] + ":"])

    if instr == "ifz":

        if register_type[arg[0]][1] == "float":
            code.append(space + space + ["lwc1 $f1, " + arg[0]])
            code.append(space + space + ["mtc1 $0, $f2"])
            code.append(space + space + ["c.eq.s $f1, $f2"])
            code.append(space + space + ["bc1t " + arg[1]])
        else:
            code.append(space + space + ["lw $t1, " + arg[0]])
            code.append(space + space + ["beq $t1, $0," + arg[1]])

    if instr == "return_nothing" or instr == "Function_End":
        if curr_function != "main":
            if instr == "return_nothing":
                is_return = 1
            if instr == "Function_End" and is_return == 1:
                pass
            else:
                code.append(space + space + ["add $sp, 4"])
                code.append(space + space + ["lw $ra, ($sp)"])
                code.append(space + space + ["jr $ra"])
    if instr == "return":
        is_return = 1
        if curr_function != "main":
            ###function return value transer saving
            if func_type[curr_function] == "float":
                if register_type[arg[0]][1] == "float":
                    code.append(space + space + ["lwc1 $f21, " + arg[0]])
                else:
                    code.append(space + space + ["lw $t1, " + arg[0]])
                    code.append(space + space + ["mtc1 $t1, $f21"])
                    code.append(space + space + ["cvt.s.w $f21,$f21"])

            else:
                if register_type[arg[0]][1] == "float":
                    code.append(space + space + ["lwc1 $f1, " + arg[0]])
                    code.append(space + space + ["cvt.w.s $f2, $f1"])
                    code.append(space + space + ["mfc1 $t8, $f2"])

                else:
                    code.append(space + space + ["lw $t8, " + arg[0]])

            code.append(space + space + ["add $sp, 4"])
            code.append(space + space + ["lw $ra, ($sp)"])
            code.append(space + space + ["jr $ra"])
        pass
    if instr == "main_end":
        code.append(space + space + ["li $v0, 10"])
        code.append(space + space + ["syscall"])
    if instr == "Function_Call":
        ###zero parameter calling function
        ### save member (normal reg) variables on the stack
        save_memb_var_on_stack(curr_function, arg[0])

        ### jal function name
        code.append(space + space + ["jal " + arg[0]])

        ### save memb var back to memory
        save_memb_var_back_to_memory(curr_function, arg[0])
        # print(curr_function)
        if len(arg) > 1:
            if func_type[arg[0]] == "float":
                # if register_type[arg[-1]][1]=="float":
                code.append(space + space + ["swc1 $f21, " + arg[-1]])
                ####if return variable and storage variable have different types
                ############################
                # else:
                #     code.append(space+space+["cvt.w.s $f2, $f1"])
                #     code.append(space+space+["mfc1 $t3, $f2"])
                #     code.append(space+space+["sw $t3, "+arg[-1]])
                pass
            else:
                # if register_type[arg[-1]][1]=="float":
                #     code.append(space+space+["mtc1 $t1, $f1"])
                #     code.append(space+space+["cvt.s.w $f1,$f1"])
                #     code.append(space+space+["swc1 $f1, "+arg[-1]])
                # else:
                code.append(space + space + ["sw $t8, " + arg[-1]])
                pass
            ##put return value to arg[-1]
        pass
    if instr == "Push_param":
        ### save member (normal reg) variables on the stack
        save_memb_var_on_stack(curr_function, arg[0])

        ### put parameters to function parameters
        if arg[-2] == "returnto":
            put_parameters_on_stack(curr_function, arg[0], arg[1:-2])
        else:
            put_parameters_on_stack(curr_function, arg[0], arg[1:])

        ### jal function name
        code.append(space + space + ["jal " + arg[0]])

        ### save memb var back to memory
        save_memb_var_back_to_memory(curr_function, arg[0])

        if arg[-2] == "returnto":
            if func_type[arg[0]] == "float":
                # if register_type[arg[-1]][1]=="float":
                ####if return variable and storage variable have different types is commented part
                ############################
                code.append(space + space + ["swc1 $f21, " + arg[-1]])
                # else:
                #     code.append(space+space+["cvt.w.s $f2, $f1"])
                #     code.append(space+space+["mfc1 $t3, $f2"])
                #     code.append(space+space+["sw $t3, "+arg[-1]])
                pass
            else:
                # if register_type[arg[-1]][1]=="float":
                #     code.append(space+space+["mtc1 $t1, $f1"])
                #     code.append(space+space+["cvt.s.w $f1,$f1"])
                #     code.append(space+space+["swc1 $f1, "+arg[-1]])
                # else:
                code.append(space + space + ["sw $t8, " + arg[-1]])
                pass
            ##put return value to arg[-1]
        pass
        # print(curr_function)
    if instr == "address_assignment":
        code.append(space + space + ["la $t1, " + arg[1]])  # reg0
        code.append(space + space + ["la $t2, " + arg[0]])  # t_reg0
        code.append(space + space + ["sw $t1, 0($t2)"])

    if instr == "pointer_deref":
        code.append(space + space + ["lw $t1, " + arg[1]])
        if register_type[arg[0]][1] != "float":
            code.append(space + space + ["lw $t2, 0($t1)"])  ### t2 contains *ptr
            code.append(space + space + ["sw $t2, " + arg[0]])
        else:
            code.append(space + space + ["lwc1 $f1, 0($t1)"])  ### f1 contains *ptr
            code.append(space + space + ["swc1 $f1, " + arg[0]])

    if instr == "var_allocation_at_ptr":
        # arg[0] = ptr
        # arg[1] = value
        code.append(space + space + ["lw $t1, " + arg[0]])
        if register_type[arg[0]][1] != "float":
            code.append(space + space + ["lw $t2, " + arg[1]])
            code.append(space + space + ["sw $t2,  0($t1)"])
        else:
            code.append(space + space + ["lwc1 $t2, " + arg[1]])
            code.append(space + space + ["swc1 $t2,  0($t1)"])

    if instr == "assign_from_array":
        array_name = arg[2]
        var_name = arg[0]
        array_offset = arg[1]
        code.append(space + space + ["la $t1, " + array_name])
        code.append(space + space + ["lw $t2, " + array_offset])
        code.append(space + space + ["la $t3, " + var_name])
        code.append(space + space + ["add $t1, $t1, $t2"])

        if (
            register_type[var_name][1] == "float"
            and register_type[array_name][1] == "float"
        ):
            code.append(space + space + ["lwc1 $f1, 0($t1)"])
            code.append(space + space + ["swc1 $f1, 0($t3)"])

        elif (
            register_type[var_name][1] != "float"
            and register_type[array_name][1] == "float"
        ):
            code.append(space + space + ["lwc1 $f1, 0($t1)"])
            code.append(space + space + ["cvt.w.s $f2, $f1"])
            code.append(space + space + ["mfc1 $t4, $f2"])
            code.append(space + space + ["sw $t4, 0($t3)"])

        elif (
            register_type[var_name][1] == "float"
            and register_type[array_name][1] != "float"
        ):
            code.append(space + space + ["lw $t4, 0($t1)"])
            code.append(space + space + ["mtc1 $t4, $f1"])
            code.append(space + space + ["cvt.s.w $f1,$f1"])
            code.append(space + space + ["swc1 $f1, 0($t3)"])

        elif (
            register_type[var_name][1] != "float"
            and register_type[array_name][1] != "float"
        ):
            code.append(space + space + ["lw $t4, 0($t1)"])
            code.append(space + space + ["sw $t4, 0($t3)"])

        pass

    if instr == "assign_to_array":
        array_name = arg[0]
        var_name = arg[2]
        array_offset = arg[1]
        code.append(space + space + ["la $t1, " + array_name])
        code.append(space + space + ["lw $t2, " + array_offset])
        code.append(space + space + ["la $t3, " + var_name])
        code.append(space + space + ["add $t1, $t1, $t2"])

        if (
            register_type[var_name][1] == "float"
            and register_type[array_name][1] == "float"
        ):
            code.append(space + space + ["lwc1 $f1, 0($t3)"])
            code.append(space + space + ["swc1 $f1, 0($t1)"])

        elif (
            register_type[var_name][1] == "float"
            and register_type[array_name][1] != "float"
        ):
            code.append(space + space + ["lwc1 $f1, 0($t3)"])
            code.append(space + space + ["cvt.w.s $f2, $f1"])
            code.append(space + space + ["mfc1 $t4, $f2"])
            code.append(space + space + ["sw $t4, 0($t1)"])

        elif (
            register_type[var_name][1] != "float"
            and register_type[array_name][1] == "float"
        ):
            code.append(space + space + ["lw $t4, 0($t3)"])
            code.append(space + space + ["mtc1 $t4, $f1"])
            code.append(space + space + ["cvt.s.w $f1,$f1"])
            code.append(space + space + ["swc1 $f1, 0($t1)"])

        elif (
            register_type[var_name][1] != "float"
            and register_type[array_name][1] != "float"
        ):
            code.append(space + space + ["lw $t4, 0($t3)"])
            code.append(space + space + ["sw $t4, 0($t1)"])

    if instr == "multiply_constant":
        code.append(space + space + ["la $t1, " + arg[0]])
        code.append(space + space + ["lw $t2, " + arg[1]])
        code.append(space + space + ["addi $t3, $0, " + arg[2]])
        code.append(space + space + ["mul $t2, $t2, $t3"])
        code.append(space + space + ["sw $t2, 0($t1)"])
        pass

    if instr == "!":
        code.append(space + space + ["lw $t1, " + arg[0]])
        code.append(space + space + ["addi $t2, $0, 1"])
        code.append(space + space + ["xor $t1, $t1, $t2"])
        code.append(space + space + ["sw $t1, " + arg[0]])

    if instr == "exit":
        code.append(space + space + ["li $v0, 4"])
        code.append(space + space + ["la $a0, Exit"])
        code.append(space + space + ["syscall"])
        code.append(space + space + ["li $v0, 10"])
        code.append(space + space + ["syscall"])


for i in register_type.keys():
    if register_type[i][1] in dtype_size.keys():
        if register_type[i][0] == "reg_array":
            code.append(
                [
                    i
                    + ": .space "
                    + str(dtype_size[register_type[i][1]] * register_type[i][2])
                ]
            )
        else:
            code.append([i + ": .space " + str(dtype_size[register_type[i][1]])])

with open("bin/mips.code") as f:
    lines = f.read().splitlines()
    for i in lines:
        lineno = lineno + 1
        string = i.split(" ")
        instr = string[0]
        instr_arg = string[1:] if len(string) > 1 else []
        if instr[:9] == "outputstr":
            code.append(instr + ":    .asciiz " + (" ").join(instr_arg))

    code.append([])
    code.append(space + [".text"])
    code.append(space + [".globl main"])
    code.append([])

    for i in lines:
        lineno = lineno + 1
        string = i.split(" ")
        instr = string[0]
        instr_arg = string[1:] if len(string) > 1 else []
        instr_arg = [i for i in instr_arg if i != ""]
        instr_classifier(instr, instr_arg)

with open("bin/mips.s", "w") as f:
    for i in code:
        f.write(("").join(i))
        f.write("\n")
