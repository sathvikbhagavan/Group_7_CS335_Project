    .data
Exit:    .asciiz "[Runtime Error] Assertion Error"
t_reg0: .space 4
reg0: .space 4
t_reg1: .space 4
reg1: .space 4
reg2: .space 4
reg3: .space 4
t_reg2: .space 4
t_reg4: .space 4
t_reg5: .space 4
outputstr0:    .asciiz "\n"

    .text
    .globl main

main:
        la $t1, reg0
        addi $t2, $0, 1
        sw $t2, 0($t1)
        la $t1, reg1
        li $t2, 0x40000000
        mtc1 $t2, $f1
        swc1 $f1,0($t1)
        la $t1, reg2
        addi $t2, $0, 0
        sw $t2, 0($t1)
        la $t1, reg3
        addi $t2, $0, 0
        sw $t2, 0($t1)
        la $t1, reg1
        la $t2, reg0
        la $t3, t_reg2
        lw $t4,0($t2)
        mtc1 $t4,$f21
        cvt.s.w $f21, $f21
        lwc1 $f20,0($t1)
        sub.s $f20, $f20, $f21
        swc1 $f20,0($t3)
        la $t1, reg2
        la $t2, t_reg2
        lwc1 $f1, 0($t2)
        cvt.w.s $f2, $f1
        mfc1 $t3, $f2
        sw $t3, 0($t1)
        la $t1, reg2
        lw $a0,0($t1)
        li $v0, 1
        syscall
        li $v0, 4
        la $a0, outputstr0
        syscall
        la $t1, reg3
        li $v0, 5
        syscall
        sw $v0,0($t1)
        la $t1, t_reg4
        addi $t2, $0, 1
        sw $t2, 0($t1)
        la $t1, reg3
        la $t2, t_reg4
        la $t3, reg3
        lw $t4,0($t1)
        lw $t5,0($t2)
        sub $t4, $t4, $t5
        sw $t4,0($t3)
        la $t1, reg3
        lw $a0,0($t1)
        li $v0, 1
        syscall
        la $t1, t_reg5
        addi $t2, $0, 0
        sw $t2, 0($t1)
        li $v0, 10
        syscall
