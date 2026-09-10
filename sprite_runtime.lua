-- A sprite variant never changes entity type, damage, velocity or target.
-- Restore native GM IDs while simulation runs; apply the variant for rendering.
local M = {}
M.one = [[
spriteOne:
    ; eax=entity id, edx=0 restore native / 1 apply custom
    pushad
    mov ebx, eax
    mov edi, [ENTITYVARIANT+ebx*4]
    test edi, edi
    jz so_done
    cmp edi, 33
    ja so_drop
    imul esi, ebx, 232
    add esi, ENTITYARRAY
    mov ecx, [ENTITYUID+ebx*4]
    cmp [esi+0x30], ecx
    jne so_clear
    cmp word [esi+0x28], 1
    jl so_clear
    cmp word [esi+0x28], 2
    ja so_clear
    movzx ecx, word [esi+0x2A]
    cmp ecx, [ENTITYTYPE+ebx*4]
    jne so_clear
    mov ecx, [VARIANTGM+edi*4]
    test ecx, ecx
    jz so_done
    movzx eax, word [esi+0x06]
    cmp eax, ecx
    je so_owned
    cmp eax, [VARIANTBASEGM+edi*4]
    jne so_clear
so_owned:
    test edx, edx
    jz so_restore
    movzx eax, word [esi+0x04]
    test eax, eax
    jz so_clear
    cmp eax, [VARIANTCOUNT+edi*4]
    ja so_clear
    mov [esi+0x06], cx
    jmp so_done
so_restore:
    mov ecx, [VARIANTBASEGM+edi*4]
    mov [esi+0x06], cx
    jmp so_done
so_clear:
    mov ecx, [ENTITYUID+ebx*4]
    cmp [esi+0x30], ecx
    jne so_drop
    mov ecx, [VARIANTGM+edi*4]
    cmp word [esi+0x06], cx
    jne so_drop
    mov ecx, [VARIANTBASEGM+edi*4]
    mov word [esi+0x06], cx
so_drop:
    mov dword [ENTITYVARIANT+ebx*4], 0
so_done:
    popad
    ret
]]
M.all = [[
spriteAll:
    ; edx=mode; bounded entity array, no target scans or Lua per frame.
    pushad
    mov eax, 1
sa_loop:
    call SPRITEONE
    inc eax
    cmp eax, 3000
    jl sa_loop
    popad
    ret
]]
M.spawn_original = [[
spriteSpawnOriginal:
    sub esp, 8
    push ebx
    mov ebx, [esp+0x34]
    jmp SPAWNRESUME
]]
M.spawn = [[
spriteSpawn:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    push dword [ebp+48]
    push dword [ebp+44]
    push dword [ebp+40]
    push dword [ebp+36]
    push dword [ebp+32]
    push dword [ebp+28]
    push dword [ebp+24]
    push dword [ebp+20]
    push dword [ebp+16]
    push dword [ebp+12]
    push dword [ebp+8]
    call SPAWNORIGINAL
    cmp eax, 1
    jl ss_done
    cmp eax, 3000
    jae ss_done
    ; Clear a recycled slot even when the new entity is not a custom shot.
    mov dword [ENTITYVARIANT+eax*4], 0
    cmp dword [REENTRY], 0
    je ss_done
    mov ebx, [CURRENTVARIANT]
    test ebx, ebx
    jz ss_done
    cmp ebx, 33
    ja ss_done
    imul esi, eax, 232
    add esi, ENTITYARRAY
    mov [ENTITYVARIANT+eax*4], ebx
    mov edx, [esi+0x30]
    mov [ENTITYUID+eax*4], edx
    movzx edx, word [esi+0x2A]
    mov [ENTITYTYPE+eax*4], edx
    mov edx, 1
    call SPRITEONE
ss_done:
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret 44
]]
M.update_original = [[
spriteUpdateOriginal:
    push ecx
    push ebx
    push ebp
    push esi
    mov esi, ecx
    jmp ENTITYRESUME
]]
M.update = [[
spriteUpdate:
    pushfd
    pushad
    xor edx, edx
    call SPRITEALL
    popad
    popfd
    call ENTITYORIGINAL
    pushfd
    pushad
    mov edx, 1
    call SPRITEALL
    if HASDECOR = 1
        call REBUILDDECOR
    end if
    popad
    popfd
    ret
]]
return M
