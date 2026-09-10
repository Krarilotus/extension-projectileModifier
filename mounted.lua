-- Horse archers have a second rendered layer but share the body's native clock.
-- Substitute a persisted weapon clock only while their native bow routine runs.
local M = {}
M.hook = [[
mountedBow:
    pushfd
    pushad
    mov ebp, esp
    mov ebx, [ebp+40]
    cmp ebx, 1
    jl mb_native
    cmp ebx, MAXUNITS
    jae mb_native
    cmp dword [NATIVEINTT+ebx*4], -1
    je mb_native
    push ebx
    call PROFILE
    add esp, 4
    cmp eax, MAXPROFILES
    jae mb_native
    mov edi, eax
    cmp dword [NATIVECYCLET+edi*4], 0
    je mb_native
    mov esi, ebx
    imul esi, esi, 0x490
    add esi, UNITARRAY
    cmp word [esi+0x8E], 74
    jne mb_native
    cmp dword [WEAPONSEENT+ebx*4], 0
    jne mb_done
    mov dword [WEAPONSEENT+ebx*4], 1
    movzx eax, word [esi+0x424]
    cmp eax, [WEAPONPHASET+ebx*4]
    je mb_save
    mov dword [WEAPONCYCLET+ebx*4], 0
    mov dword [WEAPONTICKT+ebx*4], 0
mb_save:
    ; Stack locals, not shared scratch: native dispatch may run a whole volley.
    push dword [esi+0x2B0]
    push dword [esi+0x40]
    push dword [esi+0x44]
    push dword [esi+0x3C]
    push dword [esi+0x48]
    push dword [esi+0x50]
    push dword [esi+0x58]
    push dword [esi+0x04]
    mov eax, [WEAPONCYCLET+ebx*4]
    mov [esi+0x2B0], eax
    mov eax, [WEAPONTICKT+ebx*4]
    mov [esi+0x40], eax
    mov dword [esi+0x44], 1
    mov dword [esi+0x3C], 0
    mov dword [esi+0x50], 0
    mov [S_ID], ebx
    mov [S_PROFILE], edi
    ; Hold only the weapon immediately before its native release cycle.
    cmp word [esi+0x424], 6
    jne mb_advance
    mov eax, [NATIVECYCLET+edi*4]
    dec eax
    cmp eax, [esi+0x2B0]
    jne mb_advance
    cmp dword [esi+0x40], 1
    jl mb_advance
    cmp dword [NATIVEBLOCKT+ebx*4], 0
    jne mb_update
    cmp dword [COOLDOWNT+ebx*4], 0
    jg mb_update
    cmp dword [PENDINGT+ebx*4], 0
    jg mb_update
    push edi
    push ebx
    call NATIVETARGET
    add esp, 8
    test eax, eax
    jz mb_update
mb_advance:
    inc dword [esi+0x40]
    cmp dword [esi+0x40], 1
    jle mb_update
    mov dword [esi+0x40], 0
    inc dword [esi+0x2B0]
    mov dword [esi+0x50], 1
mb_update:
    push ebx
    call HORSEORIGINAL
    add esp, 4
    mov eax, [esi+0x2B0]
    mov [WEAPONCYCLET+ebx*4], eax
    mov eax, [esi+0x40]
    mov [WEAPONTICKT+ebx*4], eax
    movzx eax, word [esi+0x424]
    mov [WEAPONPHASET+ebx*4], eax
    pop eax
    cmp word [esi+0x2C0], 4
    je mb_standing
    mov [esi+0x04], eax           ; moving body keeps its own rendered frame
mb_standing:
    pop dword [esi+0x58]
    pop dword [esi+0x50]
    pop dword [esi+0x48]
    pop dword [esi+0x3C]
    pop dword [esi+0x44]
    pop dword [esi+0x40]
    pop dword [esi+0x2B0]
mb_done:
    popad
    popfd
    ret
mb_native:
    popad
    popfd
    jmp HORSEORIGINAL
]]
M.original = [[
horseOriginal:
    push ebx
    push esi
    mov esi, [esp+0x0C]
    jmp HORSERESUME
]]
return M
