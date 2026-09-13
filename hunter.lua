-- Configured hunters use their native bow script in working state 10. The
-- native postlude assumes a deer/carcass target; it cannot accept buildings.
-- Replace only that configured shooting phase and retain the work dispatcher
-- for movement, carrying, butchering and every unconfigured hunter.
local M = {}
M.hook = [[
hunterBow:
    pushfd
    pushad
    mov ebx, [CURUNIT]
    cmp ebx, 1
    jl hb_native
    cmp ebx, MAXUNITS
    jae hb_native
    if HASMANUALONLY = 0
        cmp dword [NATIVEINTT+ebx*4], -1
        je hb_native
    end if
    push ebx
    call PROFILE
    add esp, 4
    cmp eax, MAXPROFILES
    jae hb_native
    mov edi, eax
    cmp dword [AUTOTARGETT+edi*4], 0
    jne hb_scheduled
    cmp dword [AIONLYT+edi*4], 0
    je hb_manual
    push ebx
    call ISAIOWNED
    add esp, 4
    test eax, eax
    jz hb_native
hb_manual:
    push ebx
    call MANUALORDER
    add esp, 4
    test eax, eax
    jnz hb_scheduled
    imul eax, ebx, 0x490
    cmp word [eax+UNITARRAY+0x2C0], 10
    jne hb_native              ; retain movement, carrying and other work
    jmp hb_done
hb_scheduled:
    cmp dword [NATIVEINTT+ebx*4], -1
    je hb_native
    cmp dword [NATIVECYCLET+edi*4], 0
    je hb_native
    imul esi, ebx, 0x490
    add esi, UNITARRAY
    cmp word [esi+0x2C0], 10
    jne hb_native
    mov dword [esi+0x44], 2
    mov dword [esi+0x30], 0
    mov eax, [esi+0x2B0]
    cmp eax, HUNTEREND
    jae hb_finished
    movsx eax, byte [HUNTERSCRIPT+eax]
    mov [esi+0x48], eax
    test eax, eax
    jle hb_finished
    movsx edx, word [esi+0x54]
    lea edx, [edx+eax*8+0x301]
    mov [esi+0x04], edx
    mov dword [S_FIRED], 0
    push edi
    push ebx
    call NATIVERELEASE
    add esp, 8
    cmp dword [S_FIRED], 0
    je hb_done
    movsx eax, word [esi+0xC6]
    movsx edx, word [esi+0xC4]
    push 5
    push eax
    push edx
    mov ecx, SOUNDTHIS
    call HUNTERSOUND
    jmp hb_done
hb_finished:
    mov dword [esi+0x2B0], 0
    mov word [esi+0x2C0], 0
hb_done:
    popad
    popfd
    ret
hb_native:
    popad
    popfd
    push ebx
    push ebp
    push esi
    push edi
    mov edi, [CURUNIT]
    jmp HUNTERRESUME
]]
return M
