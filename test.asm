SECTION    .data

numbers: dd 123, 312, 123123123
src: dq 123
stuff: times 100 db 0

SECTION .bss

dst: resq 1

 SECTION .text

        mov     ax,200          ; decimal
        mov     ax,0200         ; still decimal
        mov     ax,0200d        ; explicitly decimal
        mov     ax,0d200        ; also decimal
        mov     ax,0c8h         ; hex
        mov     ax,$0c8         ; hex again: the 0 is required
asd        mov     ax,0xc8         ; hex yet again
        mov     ax,0hc8         ; still hex
        mov     ax,310q         ; octal
veryverylonglabel:        mov     ax,310o         ; octal again
        mov     ax,0o310        ; octal yet again
        mov     ax,0q310        ; octal yet again
        mov     ax,11001000b    ; binary
        mov     ax,1100_1000b   ; same binary constant
abc:        mov     ax,1100_1000y   ; same binary constant once more
        mov     ax,0b1100_1000  ; same binary constant yet again
        mov     ax,0y1100_1000  ; same binary constant yet again

something:
lodsb
mov eax, 1
mov ebx,2
call something


mov si, src
mov di, dst
mov cx, 0x4
cld
rep movsb
