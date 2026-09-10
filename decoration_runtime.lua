local M = {}
M.rebuild = [[
rebuildDecorations:
    pushfd
    pushad
    cld
    mov edi, DECORGRID
    xor eax, eax
    mov ecx, 10000
    rep stosd
    mov ebx, 1
dr_loop:
    mov dword [DECORNEXT+ebx*4], 0
    mov edi, [DECORVARIANT+ebx*4]
    test edi, edi
    jz dr_next
    cmp edi, 33
    ja dr_clear
    imul esi, ebx, 232
    add esi, ENTITYARRAY
    mov eax, [DECORUID+ebx*4]
    cmp [esi+0x30], eax
    jne dr_clear
    cmp word [esi+0x28], 1
    je dr_next                  ; newborn; native braziers activate next update
    cmp word [esi+0x28], 2
    jne dr_clear
    cmp word [esi+0x2A], 14
    jne dr_clear
    movsx eax, word [esi+0x44]
    cmp eax, 399
    ja dr_next
    movsx edx, word [esi+0x46]
    cmp edx, 399
    ja dr_next
    shr eax, 2
    shr edx, 2
    imul edx, edx, 100
    add edx, eax
    mov eax, [DECORGRID+edx*4]
    mov [DECORNEXT+ebx*4], eax
    mov [DECORGRID+edx*4], ebx
    mov eax, [DECORGM+edi*4]
    test eax, eax
    jz dr_next
    mov word [esi+0x06], ax
    jmp dr_next
dr_clear:
    mov dword [DECORVARIANT+ebx*4], 0
dr_next:
    inc ebx
    cmp ebx, 3000
    jl dr_loop
    popad
    popfd
    ret
]]

M.profile = [[
decorationProfile:
    ; cdecl(unitID, baseProfile) -> effective profile. Native brazier proximity
    ; is a 3-tile Chebyshev box, not a Euclidean circle; height difference <45.
    pushad
    mov ebp, esp
    sub esp, 44
    mov eax, [ebp+40]
    mov [ebp+28], eax
    mov esi, [ebp+36]
    imul esi, esi, 0x490
    add esi, UNITARRAY
    movzx eax, word [esi+0x8E]
    cmp eax, MAXTYPES
    jae dp_done
    cmp dword [DECORRULEST+eax*4], 0
    je dp_done
    imul eax, eax, 408
    mov [ebp-16], eax
    movsx eax, word [esi+0xC4]
    cmp eax, 399
    ja dp_done
    mov [ebp-4], eax
    shr eax, 2
    dec eax
    mov [ebp-28], eax
    movsx eax, word [esi+0xC6]
    cmp eax, 399
    ja dp_done
    mov [ebp-8], eax
    shr eax, 2
    dec eax
    mov [ebp-24], eax
    mov [ebp-32], eax
    movsx eax, word [esi+0xBA]
    movsx edx, word [esi+0xBC]
    add eax, edx
    mov [ebp-12], eax
    mov dword [ebp-20], 34
    mov dword [ebp-44], 3000
dp_row:
    mov eax, [ebp-28]
    mov [ebp-36], eax
    cmp dword [ebp-32], 99
    ja dp_nextrow
dp_cell:
    mov eax, [ebp-36]
    cmp eax, 99
    ja dp_nextcell
    imul edx, [ebp-32], 100
    add eax, edx
    mov ebx, [DECORGRID+eax*4]
dp_entity:
    cmp ebx, 1
    jl dp_nextcell
    cmp ebx, 3000
    jae dp_nextcell
    dec dword [ebp-44]
    js dp_done
    mov edi, [DECORVARIANT+ebx*4]
    cmp edi, 1
    jl dp_nextentity
    cmp edi, 33
    ja dp_nextentity
    imul esi, ebx, 232
    add esi, ENTITYARRAY
    mov eax, [DECORUID+ebx*4]
    cmp [esi+0x30], eax
    jne dp_nextentity
    cmp word [esi+0x28], 2
    jne dp_nextentity
    cmp word [esi+0x2A], 14
    jne dp_nextentity
    imul edi, edi, 12
    add edi, [ebp-16]
    add edi, DECORRULEMAP
    mov eax, [edi]
    test eax, eax
    jz dp_nextentity
    cmp eax, [ebp-20]
    jge dp_nextentity
    movsx eax, word [esi+0x44]
    sub eax, [ebp-4]
    add eax, 3
    cmp eax, 6
    ja dp_nextentity
    movsx eax, word [esi+0x46]
    sub eax, [ebp-8]
    add eax, 3
    cmp eax, 6
    ja dp_nextentity
    movsx eax, word [esi+0x3C]
    sub eax, [ebp-12]
    add eax, 44
    cmp eax, 88
    ja dp_nextentity
    mov eax, [edi]
    mov [ebp-20], eax
    mov eax, [ebp+40]
    cmp eax, MAXTYPES
    mov eax, [edi+4]
    jl dp_choose
    mov eax, [edi+8]
dp_choose:
    mov [ebp+28], eax
    cmp dword [ebp-20], 1
    je dp_done
dp_nextentity:
    mov ebx, [DECORNEXT+ebx*4]
    jmp dp_entity
dp_nextcell:
    inc dword [ebp-36]
    mov eax, [ebp-28]
    add eax, 3
    cmp [ebp-36], eax
    jl dp_cell
dp_nextrow:
    inc dword [ebp-32]
    mov eax, [ebp-24]
    add eax, 3
    cmp [ebp-32], eax
    jl dp_row
dp_done:
    mov esp, ebp
    popad
    ret
]]

M.native_filter = [[
filterNativeBrazier:
    ; EDI=entity ID, ESI=&entity.type in the original proximity scan.
    pushfd
    pushad
    cmp edi, 1
    jl db_native
    cmp edi, 3000
    jae db_native
    cmp dword [DECORVARIANT+edi*4], 0
    je db_native
    mov eax, [esi+6]
    cmp eax, [DECORUID+edi*4]
    jne db_native
    popad
    popfd
    jmp BRAZIERNEXT
db_native:
    popad
    popfd
    cmp word [esi], 14
    jne db_skip
    jmp BRAZIERRESUME
db_skip:
    jmp BRAZIERNEXT
]]
return M
