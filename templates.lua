-- FASM sources for the injected routines, split to fit UCP's assembler budget.
-- Value mapping supplied by init.lua.

return {

-- accuracySet(unitID): explicit regular-ammunition accuracy, respecting AI-only
-- and fortification overrides. Native cow orders keep their original accuracy.
accuracy_set_code = [[
accuracySet:
    push ebx
    mov ebx, [esp+8]
    push ebx
    call PROFILE
    add esp, 4
    cmp eax, MAXPROFILES
    jae ac_no
    cmp dword [INACCSETT+eax*4], 0
    je ac_no
    cmp dword [AIONLYT+eax*4], 0
    je ac_ownerok
    push ebx
    call ISAIOWNED
    add esp, 4
    test eax, eax
    jz ac_no
ac_ownerok:
    imul ebx, ebx, 0x490
    cmp word [ebx+UNITARRAY+0x3B0], 0
    jne ac_no
    mov eax, 1
    pop ebx
    ret
ac_no:
    xor eax, eax
    pop ebx
    ret
]],

-- Replace the native ground scatter with its exact input point. Applying the
-- configured radius later, once per projectile, avoids repeated native drift.
ground_aim_hook_code = [[
groundAimHook:
    pushad
    mov ebp, esp
    push dword [ebp+0x24]
    call ACCURACYSET
    add esp, 4
    test eax, eax
    jz ga_pass
    mov eax, [ebp+0x24]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    mov ecx, [ebp+0x28]
    mov word [eax+0xBE], cx
    mov ecx, [ebp+0x2C]
    mov word [eax+0xC0], cx
    mov ecx, [ebp+0x30]
    mov word [eax+0xC2], cx
    popad
    ret 0x10
ga_pass:
    popad
    push ecx
    mov eax, [esp+8]
    jmp RESUME
]],

-- ESI = UnitState + unitID*stride here. Target prediction is complete; only
-- the native random error remains. Return with the original function's ABI.
aim_error_hook_code = [[
aimErrorHook:
    pushad
    mov eax, esi
    sub eax, UNITSTATE
    xor edx, edx
    mov ecx, 0x490
    div ecx
    push eax
    call ACCURACYSET
    add esp, 4
    test eax, eax
    jz ae_pass
    popad
    pop edi
    pop esi
    pop ebp
    ret 0xC
ae_pass:
    popad
    movzx eax, word [esi+0x6CE]
    jmp RESUME
]],

-- profile(unitID) -> table index. Preserve other registers. Positive structure
-- height AND the native wall/fortification tile flags distinguish standing on
-- the structure from terrain elevation or standing on the ground beside it.
profile_code = [[
profile:
    push ebx
    push ecx
    push edx
    mov eax, [esp+16]
    cmp eax, 1
    jl pf_invalid
    cmp eax, MAXUNITS
    jge pf_invalid
    imul eax, eax, 0x490
    add eax, UNITARRAY
    mov ebx, eax
    movzx eax, word [ebx+0x8E]
    cmp eax, MAXTYPES
    jae pf_invalid
    cmp dword [FORTIFIEDT+eax*4], 0
    je pf_done
    cmp word [ebx+0xBC], 0
    jle pf_done
    movsx ecx, word [ebx+0xC4]
    cmp ecx, 399
    ja pf_done
    movsx edx, word [ebx+0xC6]
    cmp edx, 399
    ja pf_done
    lea edx, [edx+edx*2]
    mov edx, [TILEROWS+edx*4]
    add edx, ecx
    cmp edx, 80400
    jae pf_done
    test dword [TILEFLAGS+edx*4], 0x10000100
    jz pf_done
    add eax, MAXTYPES
    jmp pf_done
pf_invalid:
    mov eax, MAXPROFILES
pf_done:
    cmp eax, MAXPROFILES
    jae pf_return
    mov ecx, [esp+16]
    cmp dword [PROFILESTATET+ecx*4], eax
    je pf_return
    mov [PROFILESTATET+ecx*4], eax
    ; Do not release an old conditional volley after stepping off its trigger.
    ; Keep the main cooldown so changing ground/wall state cannot bypass reload.
    mov dword [PENDINGT+ecx*4], 0
    mov dword [PENDCDT+ecx*4], 0
    mov dword [SYNCWAITT+ecx*4], 0
pf_return:
    pop edx
    pop ecx
    pop ebx
    ret
]],

-- Shared helpers plus the volley routine.
--   volley(unitID, entityType, x, y, z, count, spread)  -- cdecl, caller cleans
-- Sets REENTRY while it runs so the fire hook lets our own shots through.
volley_code = [[
; volley(unitID, entityType, x, y, z, count, spread) -- cdecl, caller cleans.
; Sets REENTRY while it runs so the fire hook lets our own shots straight through.
; Callers set S_HEIGHT and S_MULTI first; S_MULTI needs the candidate list that
; scanUnit leaves behind.
volley:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov dword [REENTRY], 1
    ; Raise the firing point. The game reads the origin height straight off the
    ; shooter, so lifting buildingHeight for the duration of the volley is the
    ; way to shoot from the top of a siege tower rather than from its feet.
    mov eax, [ebp+0x08]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    mov [S_SHOOTER], eax
    movzx ecx, word [eax+0x3B0]
    mov [S_SAVECOW], ecx
    cmp dword [S_EXPLICIT], 0
    je v_keepcow
    mov word [eax+0x3B0], 0
v_keepcow:
    movsx ecx, word [eax+0xBC]
    mov [S_SAVEBH], ecx
    add ecx, [S_HEIGHT]
    mov word [eax+0xBC], cx
    mov esi, [ebp+0x1C]
    cmp esi, 1
    jge v_ok
    mov esi, 1
v_ok:
    xor edi, edi
v_loop:
    mov eax, [ebp+0x10]
    mov [S_SHOTX], eax
    mov eax, [ebp+0x14]
    mov [S_SHOTY], eax
    mov eax, [ebp+0x18]
    mov [S_SHOTZ], eax
    cmp dword [S_MULTI], 0
    je v_scatter
    mov ecx, [S_NCAND]
    test ecx, ecx
    jz v_scatter
    ; pick a fresh victim for this projectile
    call RND
    xor edx, edx
    div ecx
    mov eax, [S_CANDS+edx*4]
    mov ebx, eax
    imul ebx, ebx, 0x490
    add ebx, UNITARRAY
    movsx ecx, word [ebx+0xB6]
    mov [S_SHOTX], ecx
    movsx ecx, word [ebx+0xB8]
    mov [S_SHOTY], ecx
    movsx ecx, word [ebx+0xBA]
    movsx edx, word [ebx+0xBC]
    add ecx, edx
    add ecx, 30
    mov [S_SHOTZ], ecx
    ; aim the shooter at this victim, otherwise the projectile damages whoever
    ; the previous shot was aimed at
    mov edx, [S_SHOOTER]
    mov word [edx+0x344], ax
    mov ecx, [ebx+0x98]
    mov [edx+0xA0], ecx
    ; fall through: a random victim is still aimed at imperfectly
v_scatter:
    mov dword [S_MOVED], 0
    mov ecx, [S_INACC]
    test ecx, ecx
    jz v_fan
v_disk:
    call scat
    mov [SCATY], eax
    mov ecx, [S_INACC]
    call scat
    mov ebx, eax
    imul ebx, ebx
    mov edx, [SCATY]
    imul edx, edx
    add ebx, edx
    mov ecx, [S_INACC]
    mov edx, ecx
    imul edx, edx
    cmp ebx, edx
    ja v_disk
    mov edx, [SCATY]
    add [S_SHOTX], edx
    add [S_SHOTY], eax
    mov dword [S_MOVED], 1
v_fan:
    cmp dword [S_MULTI], 0
    jne v_settle                  ; random targets: each shot is aimed properly
    test edi, edi
    jz v_settle
    mov ecx, [ebp+0x20]
    test ecx, ecx
    jz v_settle
    call scat
    add [S_SHOTX], eax
    mov ecx, [ebp+0x20]
    call scat
    add [S_SHOTY], eax
    mov dword [S_MOVED], 1
v_settle:
    cmp dword [S_MOVED], 0
    je v_fire
    call FIXSCATTER
v_fire:
    ; Cow is an output entity type, not a native unit-dispatch mode. Route it
    ; through the siege cow path for its launch height, muzzle and ground-target
    ; metadata. The generic path would give it arrow-style target/height data.
    mov eax, [ebp+0x0C]
    cmp eax, 23
    jne v_dispatch
    mov edx, [S_SHOOTER]
    mov word [edx+0x3B0], 1
    mov eax, 2
    cmp word [edx+0x8E], 40
    jne v_dispatch
    mov eax, 3
v_dispatch:
    push dword [S_SHOTZ]
    push dword [S_SHOTY]
    push dword [S_SHOTX]
    push eax
    push dword [ebp+0x08]
    mov ecx, UNITSTATE
    call FIREPROJ
    inc edi
    cmp edi, esi
    jl v_loop
    mov dword [REENTRY], 0
    mov eax, [S_SHOOTER]
    mov ecx, [S_SAVEBH]
    mov word [eax+0xBC], cx
    mov ecx, [S_SAVECOW]
    mov word [eax+0x3B0], cx
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret

; ecx = spread -> eax in [-spread, +spread]
scat:
    push ebx
    push ecx
    call RND
    pop ecx
    lea ebx, [ecx*2+1]
    xor edx, edx
    div ebx
    sub edx, ecx
    mov eax, edx
    pop ebx
    ret
]],

-- Entry hook on the game's "unit fires a projectile" dispatcher.
-- Entry stack: [esp]=ret [+4]=unitID [+8]=entityType [+0xC]=x [+0x10]=y [+0x14]=z
-- rnd -> eax in [0, 0x7FFF). Clobbers eax and edx only, so a caller may keep
-- anything it needs in ecx or a callee-saved register across the call.
-- fixScatter: after an aim point has been nudged, pull it back onto the map and
-- take the ground height there. Without this the shot keeps the height of the
-- thing it was originally aimed at, and an arcing projectile - a catapult or
-- trebuchet rock - is asked to reach a point that is not on the ground. The
-- solver has no answer and the rock never appears.
fixscatter_code = [[
fixScatter:
    push ebx
    mov eax, [S_SHOTX]
    cmp eax, 8
    jge fs_xlo
    mov eax, 8
fs_xlo:
    cmp eax, MAPMICROMAX
    jle fs_xhi
    mov eax, MAPMICROMAX
fs_xhi:
    mov [S_SHOTX], eax
    mov ecx, [S_SHOTY]
    cmp ecx, 8
    jge fs_ylo
    mov ecx, 8
fs_ylo:
    cmp ecx, MAPMICROMAX
    jle fs_yhi
    mov ecx, MAPMICROMAX
fs_yhi:
    mov [S_SHOTY], ecx
    sar eax, 3
    sar ecx, 3
    mov edx, ecx
    lea edx, [edx+edx*2]
    mov edx, [edx*4+TILEROWS]
    add edx, eax
    movzx ebx, byte [edx+TERRAINH]
    mov [S_SHOTZ], ebx
    pop ebx
    ret
]],

rand_code = [[
rnd:
    mov eax, [SEED]
    imul eax, eax, 1103515245
    add eax, 12345
    mov [SEED], eax
    shr eax, 16
    and eax, 0x7FFF
    ret
]],

-- setStagger(unitID, unitType) -- cdecl. Rolls the wait before this unit's next
-- staggered projectile and stores it.
stagger_code = [[
setStagger:
    push ebp
    mov ebp, esp
    push ebx
    mov ebx, [ebp+0x0C]
    mov ecx, [STAGMAXT+ebx*4]
    sub ecx, [STAGMINT+ebx*4]
    inc ecx
    cmp ecx, 1
    jge ss_span
    mov ecx, 1
ss_span:
    mov [S_TMP], ecx
    call RND
    xor edx, edx
    div dword [S_TMP]
    mov eax, edx
    add eax, [STAGMINT+ebx*4]
    cmp eax, 1
    jge ss_store
    mov eax, 1
ss_store:
    mov ecx, [ebp+0x08]
    mov [PENDCDT+ecx*4], eax
    pop ebx
    pop ebp
    ret
]],

-- chooseInterval(unitID, unitType) -> eax = ticks between shots in the unit's
-- current state, or 0 if it should hold fire. Works out whether the unit is
-- moving and whether it is fixed to a wall, since both change the rate.
interval_code = [[
chooseInterval:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, [ebp+0x08]
    mov edx, [ebp+0x0C]
    ; Is this unit actually moving? The game has no "walking" flag, so compare
    ; its interpolated position with last tick's. A slow unit does not advance
    ; every single tick, so a change keeps it counted as moving for a while.
    mov esi, eax
    imul esi, esi, 0x490
    add esi, UNITARRAY
    movzx ecx, word [esi+0xB6]
    shl ecx, 16
    movzx edi, word [esi+0xB8]
    or ecx, edi
    cmp ecx, [LASTPOST+eax*4]
    mov [LASTPOST+eax*4], ecx
    je ci_still
    mov dword [MOVECDT+eax*4], MOVEHYST
    jmp ci_known
ci_still:
    mov ecx, [MOVECDT+eax*4]
    test ecx, ecx
    jz ci_known
    dec ecx
    mov [MOVECDT+eax*4], ecx
ci_known:
    cmp dword [MOVECDT+eax*4], 0
    jne ci_moving
    mov ebx, [ISTANDT+edx*4]
    jmp ci_state
ci_moving:
    mov ebx, [IMOVET+edx*4]
ci_state:
    push edx
    push eax
    call CHECKATTACHED
    add esp, 4
    pop edx
    mov eax, [ebp+0x08]
    cmp dword [S_ATTACHED], 0
    je ci_done
    mov ecx, [ATTINTT+edx*4]
    cmp ecx, -1
    je ci_done                    ; -1 means "same rate as usual"
    mov ebx, ecx
ci_done:
    mov eax, ebx
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret
]],

-- crewOk(unitID, unitType) -> eax = 1 when the unit may shoot. Siege engines
-- need their current crew aboard, unless the engine is fixed to a wall and configured to carry on
-- without it.
crew_code = [[
crewOk:
    push ebp
    mov ebp, esp
    push esi
    push edi
    mov eax, [ebp+0x08]
    mov edx, [ebp+0x0C]
    ; A siege engine only shoots while its crew is aboard. The cooldown is left
    ; untouched while unmanned, so it opens fire as soon as engineers arrive.
    ; References and the lifetime "engineers sent" count are not crew aboard.
    mov ecx, [MANNEDT+edx*4]
    test ecx, ecx
    jz ck_yes
    cmp dword [S_ATTACHED], 0
    je ck_count
    cmp dword [ATTCREWT+edx*4], 0
    jne ck_yes                  ; fixed to a wall: crew no longer required
ck_count:
    mov esi, [ebp+0x08]
    imul esi, esi, 0x490
    add esi, UNITARRAY
    movsx edi, word [esi+0x3B4]
    cmp edi, ecx
    jl ck_no
ck_yes:
    mov eax, 1
    pop edi
    pop esi
    pop ebp
    ret
ck_no:
    xor eax, eax
    pop edi
    pop esi
    pop ebp
    ret
]],

fire_hook_code = [[
    cmp dword [REENTRY], 0
    jne h_pass
    pushad
    mov ebp, esp
    mov eax, [ebp+0x24]
    cmp eax, 1
    jl h_pop
    cmp eax, MAXUNITS
    jge h_pop
    push eax
    call PROFILE
    add esp, 4
    cmp eax, MAXPROFILES
    jae h_pop
    cmp dword [AIONLYT+eax*4], 0
    je h_notaionly
    push eax
    push dword [ebp+0x24]
    call ISAIOWNED
    add esp, 4
    mov ecx, eax
    pop eax
    test ecx, ecx
    jz h_pop                      ; the player's own unit: do not touch its shot
h_notaionly:
    ; Select the ammunition slot BEFORE remapping. A rock-to-mangonel change
    ; must not replace a player's cow order or multiply its native single cow.
    cmp dword [ebp+0x28], 23
    je h_cow
    cmp dword [ebp+0x28], 2
    je h_checkcow
    cmp dword [ebp+0x28], 3
    jne h_regular
h_checkcow:
    mov ebx, [ebp+0x24]
    imul ebx, ebx, 0x490
    cmp word [ebx+UNITARRAY+0x3B0], 0
    jne h_cow
h_regular:
    cmp dword [NATIVECYCLET+eax*4], 0
    je h_unscheduled
    push eax
    push dword [ebp+0x24]
    call NATIVERELEASE
    add esp, 8
    jmp h_block
h_unscheduled:
    cmp dword [SUPPRESST+eax*4], 0
    jne h_block
    mov ecx, [REMAPT+eax*4]
    mov edx, [COUNTT+eax*4]
    jmp h_count
h_cow:
    mov ecx, [COWREMAPT+eax*4]
    mov edx, [COWCOUNTT+eax*4]
    test edx, edx
    jnz h_count
    cmp ecx, -1
    je h_pop                      ; completely preserve unconfigured cow shots
    mov edx, 1
h_count:
    test edx, edx
    jz h_nocount
    ; The native mangonel dispatches seven projectiles in one update. A count
    ; replaces that volley instead of multiplying each of its seven calls.
    mov ebx, [ebp+0x24]
    cmp dword [NATIVESEENT+ebx*4], 0
    jne h_block
    mov dword [NATIVESEENT+ebx*4], 1
    jmp h_fire
h_nocount:
    cmp ecx, -1
    jne h_single
    cmp dword [HEIGHTT+eax*4], 0
    jne h_single
    cmp dword [INACCT+eax*4], 0
    je h_pop
h_single:
    mov edx, 1
h_fire:
    mov dword [S_EXPLICIT], 0
    cmp ecx, -1
    je h_originaltype
    mov dword [S_EXPLICIT], 1
    jmp h_type
h_originaltype:
    mov ecx, [ebp+0x28]
h_type:
    mov ebx, [HEIGHTT+eax*4]
    mov [S_HEIGHT], ebx
    mov dword [S_MULTI], 0
    mov ebx, [INACCT+eax*4]
    mov [S_INACC], ebx
    push dword [SPREADT+eax*4]
    push edx
    push dword [ebp+0x34]
    push dword [ebp+0x30]
    push dword [ebp+0x2C]
    push ecx
    push dword [ebp+0x24]
    call VOLLEY
    add esp, 28
h_block:
    popad
    mov ecx, [esp]
    add esp, 0x18
    xor eax, eax
    jmp ecx
h_pop:
    popad
h_pass:
    push ebx
    push esi
    push edi
    mov edi, [esp+0x14]
    jmp RESUME
]],

-- Target picking for forced shooters.
--   pickTarget(unitID, unitType) -> eax = 1 when a target was set, 0 otherwise
-- Saves the unit's own targeting fields first; restoreTarget puts them back so
-- driving a unit's aim never disturbs the order it was actually given.
pick_code = [[
pickTarget:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, [ebp+0x08]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    mov [S_UNITPTR], eax
    mov esi, eax
    movzx ecx, word [esi+0x39C]
    mov [S_SAVE0], ecx
    movzx ecx, word [esi+0x336]
    mov [S_SAVE1], ecx
    movzx ecx, word [esi+0x39E]
    mov [S_SAVE2], ecx
    mov ecx, [esi+0x3A0]
    mov [S_SAVE3], ecx
    movzx ecx, word [esi+0x3E8]
    mov [S_SAVE4], ecx
    movzx ecx, word [esi+0x3EA]
    mov [S_SAVE5], ecx
    movzx ecx, word [esi+0x344]
    mov [S_SAVE6], ecx
    mov ecx, [esi+0xA0]
    mov [S_SAVE7], ecx
    mov ecx, [esi+0xBE]
    mov [S_SAVEXY], ecx
    movzx ecx, word [esi+0xC2]
    mov [S_SAVEZ], ecx
    mov ecx, [esi+0x3A8]
    mov [S_SAVETILE], ecx
    mov ecx, [ebp+0x08]
    mov [S_SELF], ecx
    mov dword [S_NCAND], 0
    movsx ecx, word [esi+0xC4]
    mov [S_TX], ecx
    movsx ecx, word [esi+0xC6]
    mov [S_TY], ecx
    movzx ecx, word [esi+0x96]
    mov [S_OWNER], ecx
    cmp ecx, 8
    jbe pk_teamok
    xor ecx, ecx
pk_teamok:
    mov ecx, [TEAMTBL+ecx*4]
    mov [S_TEAM], ecx
    mov edx, [ebp+0x0C]
    mov ecx, [RANGET+edx*4]
    mov [S_R], ecx
    mov eax, ecx
    imul eax, ecx
    mov [S_R2], eax
    mov ecx, [WALLMINT+edx*4]
    mov eax, ecx
    imul eax, ecx
    mov [S_WMIN2], eax
    mov ebx, edx
    shl ebx, 2
    add ebx, ORDERT
    xor edi, edi
pk_next:
    mov dword [S_NCAND], 0
    cmp edi, 4
    jge pk_fail
    movzx ecx, byte [ebx+edi]
    inc edi
    test ecx, ecx
    jz pk_fail
    cmp ecx, 1
    je pk_units
    cmp ecx, 2
    je pk_walls
    cmp ecx, 5
    je pk_cluster
    mov [S_CLASS], ecx
    call SCANBLD
    test eax, eax
    jz pk_next
    mov esi, [S_UNITPTR]
    mov word [esi+0x336], ax
    mov ecx, eax
    imul ecx, ecx, 0x32C
    add ecx, BLDBASE
    mov ecx, [ecx+0xD8]
    mov [esi+0x3A0], ecx
    mov word [esi+0x39C], 9
    jmp pk_ok
pk_cluster:
    mov edx, [ebp+0x0C]
    mov ecx, [DRADT+edx*4]
    mov eax, ecx
    imul eax, ecx
    mov [S_DR2], eax
    mov ecx, [DMINT+edx*4]
    mov [S_DMIN], ecx
    call SCANUNIT
    call SCANCLUSTER
    test eax, eax
    jz pk_next
    jmp pk_aim

pk_units:
    call SCANUNIT
    test eax, eax
    jz pk_next
pk_aim:
    mov esi, eax
    imul esi, esi, 0x490
    add esi, UNITARRAY            ; esi = target unit
    mov edx, [S_UNITPTR]          ; edx = shooter
    movzx ecx, word [esi+0xB6]
    mov word [edx+0xBE], cx       ; shootTargetMicroX
    movzx ecx, word [esi+0xB8]
    mov word [edx+0xC0], cx       ; shootTargetMicroY
    movsx ecx, word [esi+0xBA]
    movsx ebx, word [esi+0xBC]
    add ecx, ebx
    mov word [edx+0xC2], cx       ; shootTargetZ
    mov word [edx+0x344], ax      ; shootTargetedUnit - the projectile's victim
    mov ecx, [esi+0x98]
    mov [edx+0xA0], ecx           ; target uid
    mov eax, 1                    ; mode 1: coordinates are ready
    jmp pk_out
pk_walls:
    call SCANWALL
    test eax, eax
    jz pk_next
    mov esi, [S_UNITPTR]
    mov ecx, [S_WX]
    mov word [esi+0x3E8], cx
    mov ecx, [S_WY]
    mov word [esi+0x3EA], cx
    mov word [esi+0x39C], 0x17
    jmp pk_ok
pk_ok:
    mov eax, 2                    ; mode 2: let acquireShootTarget fill the coords
    jmp pk_out
pk_fail:
    xor eax, eax
pk_out:
    pop edi
    pop esi
    pop ebx
    pop ebp
    ret

]],

-- restoreTarget: puts the unit's own targeting fields back.
restore_code = [[
restoreTarget:
    push esi
    mov esi, [S_UNITPTR]
    mov ecx, [S_SAVE0]
    mov word [esi+0x39C], cx
    mov ecx, [S_SAVE1]
    mov word [esi+0x336], cx
    mov ecx, [S_SAVE2]
    mov word [esi+0x39E], cx
    mov ecx, [S_SAVE3]
    mov [esi+0x3A0], ecx
    mov ecx, [S_SAVE4]
    mov word [esi+0x3E8], cx
    mov ecx, [S_SAVE5]
    mov word [esi+0x3EA], cx
    mov ecx, [S_SAVE6]
    mov word [esi+0x344], cx
    mov ecx, [S_SAVE7]
    mov [esi+0xA0], ecx
    mov ecx, [S_SAVEXY]
    mov [esi+0xBE], ecx
    mov ecx, [S_SAVEZ]
    mov word [esi+0xC2], cx
    mov ecx, [S_SAVETILE]
    mov [esi+0x3A8], ecx
    pop esi
    ret
]],

-- scanners used by pickTarget; appended to the pick_code blob at assembly time.
scan_unit_code = [[
scanUnit:
    push ebx
    push esi
    push edi
    push ebp
    mov eax, [S_R2]
    mov [S_BESTD], eax
    mov dword [S_BEST], 0
    mov ebp, [S_TEAM]
    mov edi, 1
su_loop:
    mov esi, edi
    imul esi, esi, 0x490
    add esi, UNITARRAY
    cmp word [esi+0x8C], 2        ; only normal, living units
    jne su_next
    cmp dword [esi+0x3C8], 0
    jle su_next
    cmp word [esi+0x2A0], 0      ; native acquireShootTarget eligibility
    jne su_next
    movzx ecx, word [esi+0x2C0]
    cmp ecx, 0x6F               ; native dying states 111..116
    jl su_stateok
    cmp ecx, 0x75               ; plus native excluded state 117
    jle su_next
su_stateok:
    cmp edi, [S_SELF]
    je su_next
    movzx ecx, word [esi+0x96]    ; owner
    test ecx, ecx
    jz su_next
    cmp ecx, 8
    ja su_next
    mov ecx, [TEAMTBL+ecx*4]
    cmp ecx, ebp
    je su_next                    ; same team, leave it alone
    movsx eax, word [esi+0xC4]
    sub eax, [S_TX]
    imul eax, eax
    movsx ecx, word [esi+0xC6]
    sub ecx, [S_TY]
    imul ecx, ecx
    add eax, ecx
    cmp eax, [S_R2]
    jge su_next
    ; in range: remember it as a candidate for random-target volleys
    mov ecx, [S_NCAND]
    cmp ecx, MAXCAND
    jge su_nocand
    mov [S_CANDS+ecx*4], edi
    inc ecx
    mov [S_NCAND], ecx
su_nocand:
    cmp eax, [S_BESTD]
    jge su_next
    mov [S_BESTD], eax
    mov [S_BEST], edi
su_next:
    inc edi
    cmp edi, MAXUNITS
    jl su_loop
    mov eax, [S_BEST]
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
]],

-- scanCluster -> eax = the candidate unit with the most other enemies within
-- [S_DR2] of it, or 0 if the best cluster is smaller than [S_DMIN].
-- Runs over the candidate list scanUnit leaves behind, so call that first.
scan_cluster_code = [[
scanCluster:
    push ebx
    push esi
    push edi
    push ebp
    mov dword [S_BEST], 0
    mov dword [S_BESTD], 0
    xor edi, edi
sc_outer:
    cmp edi, [S_NCAND]
    jge sc_done
    mov eax, [S_CANDS+edi*4]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    movsx ebx, word [eax+0xC4]
    movsx ebp, word [eax+0xC6]
    mov dword [S_TMP], 0
    xor esi, esi
sc_inner:
    cmp esi, [S_NCAND]
    jge sc_counted
    mov eax, [S_CANDS+esi*4]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    movsx ecx, word [eax+0xC4]
    sub ecx, ebx
    imul ecx, ecx
    movsx edx, word [eax+0xC6]
    sub edx, ebp
    imul edx, edx
    add ecx, edx
    cmp ecx, [S_DR2]
    jg sc_nextj
    inc dword [S_TMP]
sc_nextj:
    inc esi
    jmp sc_inner
sc_counted:
    mov ecx, [S_TMP]
    cmp ecx, [S_BESTD]
    jle sc_nexti
    mov [S_BESTD], ecx
    mov eax, [S_CANDS+edi*4]
    mov [S_BEST], eax
sc_nexti:
    inc edi
    jmp sc_outer
sc_done:
    mov ecx, [S_BESTD]
    cmp ecx, [S_DMIN]
    jl sc_fail
    mov eax, [S_BEST]
    jmp sc_out
sc_fail:
    xor eax, eax
sc_out:
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
]],

-- checkAttached(unitID) -> eax = 1 when this unit is fixed to a live building,
-- which for a siege tower means it has reached a wall and become the structure
-- soldiers climb. The game ties the two together through the unit's workplace
-- field and tears the building down when the unit dies, so a live link is
-- exactly "still attached and still standing".
attach_code = [[
checkAttached:
    mov dword [S_ATTACHED], 0
    mov eax, [esp+0x04]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    cmp word [eax+0x8E], 58       ; only a siege tower can be attached
    jne ca_no
    movzx ecx, word [eax+0x338]
    test ecx, ecx
    jz ca_no
    cmp ecx, MAXBLD
    jae ca_no
    imul ecx, ecx, 0x32C
    add ecx, BLDBASE
    cmp word [ecx+0xD0], 0
    je ca_no
    cmp word [ecx+0xD2], 69
    jne ca_no
    mov edx, [ecx+0xD8]
    cmp edx, [eax+0x368]
    jne ca_no
    mov dword [S_ATTACHED], 1
    mov eax, 1
    ret
ca_no:
    xor eax, eax
    ret
]],

-- isBoarded -> eax = 1 when any in-range enemy is standing within [S_BR2] of the
-- shooter, i.e. enemies have got onto the structure. Uses the candidate list
-- scanUnit leaves behind.
board_code = [[
isBoarded:
    push ebx
    push edi
    xor edi, edi
ib_loop:
    cmp edi, [S_NCAND]
    jge ib_no
    mov eax, [S_CANDS+edi*4]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    movsx ecx, word [eax+0xC4]
    sub ecx, [S_TX]
    imul ecx, ecx
    movsx edx, word [eax+0xC6]
    sub edx, [S_TY]
    imul edx, edx
    add ecx, edx
    cmp ecx, [S_BR2]
    jle ib_yes
    inc edi
    jmp ib_loop
ib_yes:
    mov eax, 1
    jmp ib_out
ib_no:
    xor eax, eax
ib_out:
    pop edi
    pop ebx
    ret
]],

-- isAiOwned(unitID) -> eax = 1 when the unit belongs to an AI lord. The game
-- stores 0 as the AI character index for a human player, which is the whole
-- test.
aiowned_code = [[
isAiOwned:
    mov eax, [esp+0x04]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    movzx eax, word [eax+0x96]
    test eax, eax
    jz ia_no
    cmp eax, 8
    ja ia_no
    imul eax, eax, 0x39F4
    mov eax, [eax+PLAYERAIC]
    test eax, eax
    jz ia_no
    mov eax, 1
    ret
ia_no:
    xor eax, eax
    ret
]],

-- wantsCow(unitID) -> eax = 1 when this unit belongs to an AI whose character
-- file permits diseased cows. The game keeps the AI character a player is using
-- at [player*0x39F4 + PLAYERAIC], where 0 means a human, and the character's
-- fields one 0x2A4 block earlier than the array base (the index is 1-based).
-- Field 141 is CowThrowInterval: 0 means that lord never throws cows.
aicow_code = [[
wantsCow:
    mov eax, [esp+0x04]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    movzx eax, word [eax+0x96]
    test eax, eax
    jz wc_no
    cmp eax, 8
    ja wc_no
    imul eax, eax, 0x39F4
    mov eax, [eax+PLAYERAIC]
    test eax, eax
    jz wc_no
    imul eax, eax, 0x2A4
    mov eax, [eax+AICCOW]
    test eax, eax
    jz wc_no
    mov eax, 1
    ret
wc_no:
    xor eax, eax
    ret
]],

-- Select automatic ammunition using the active profile in edx. Keep this in a
-- separate blob so the tick hook stays within UCP's assembler memory budget.
ammo_code = [[
chooseAmmo:
    pushad
    mov ecx, [FORCEDT+edx*4]
    mov [S_PROJ], ecx
    mov ecx, [COUNTT+edx*4]
    test ecx, ecx
    jnz ca_regularcount
    cmp dword [NATIVECYCLET+edx*4], 0
    je ca_regularcount
    mov eax, [S_ID]
    imul eax, eax, 0x490
    cmp word [eax+UNITARRAY+0x8E], 41
    jne ca_regularcount
    mov ecx, 7                   ; native mangonel volley when count is omitted
ca_regularcount:
    mov [S_VOLLEYCOUNT], ecx
    cmp dword [AICOWT+edx*4], 0
    je ca_done
    cmp dword [S_MODE], 1
    jne ca_done
    push edx
    push dword [S_ID]
    call WANTSCOW
    add esp, 4
    pop edx
    test eax, eax
    jz ca_done
    mov ecx, [COWREMAPT+edx*4]
    cmp ecx, -1
    jne ca_cowtype
    mov ecx, 23
ca_cowtype:
    mov [S_PROJ], ecx
    mov ecx, [COWCOUNTT+edx*4]
    mov [S_VOLLEYCOUNT], ecx
ca_done:
    cmp dword [S_VOLLEYCOUNT], 1
    jge ca_return
    mov dword [S_VOLLEYCOUNT], 1
ca_return:
    popad
    ret
]],

-- syncReady(unitID, unitType) -> eax = 1 when the shot may leave now.
-- With sync on, a ready shot waits for the unit's animation to come round --
-- the game raises animationCycleNumberHasJustIncremented (unit+0x50) on the
-- tick a cycle wraps -- so the projectile leaves in step with what the unit is
-- visibly doing instead of at an arbitrary frame. A unit whose animation never
-- wraps gives up after SYNCMAXT ticks and fires anyway.
sync_code = [[
syncReady:
    push ebp
    mov ebp, esp
    push ebx
    mov ebx, [ebp+0x0C]
    cmp dword [SYNCT+ebx*4], 0
    je sr_yes
    mov eax, [ebp+0x08]
    mov ecx, eax
    imul ecx, ecx, 0x490
    add ecx, UNITARRAY
    cmp dword [ecx+0x50], 0
    jne sr_reset
    mov ecx, [SYNCWAITT+eax*4]
    inc ecx
    mov [SYNCWAITT+eax*4], ecx
    cmp ecx, [SYNCMAXT+ebx*4]
    jl sr_no
sr_reset:
    mov dword [SYNCWAITT+eax*4], 0
sr_yes:
    mov eax, 1
    pop ebx
    pop ebp
    ret
sr_no:
    xor eax, eax
    pop ebx
    pop ebp
    ret
]],

scan_bld_code = [[
; nearest enemy building of class [S_CLASS] within [S_R2] -> eax = index or 0
scanBld:
    push ebx
    push esi
    push edi
    push ebp
    mov eax, [S_R2]
    mov [S_BESTD], eax
    mov dword [S_BEST], 0
    mov edi, 1
sb_loop:
    mov esi, edi
    imul esi, esi, 0x32C
    add esi, BLDBASE
    cmp word [esi+0xD0], 0
    je sb_next
    movzx ecx, word [esi+0xD6]
    test ecx, ecx
    jz sb_next
    cmp ecx, 8
    ja sb_next
    mov ecx, [TEAMTBL+ecx*4]
    cmp ecx, [S_TEAM]
    je sb_next                    ; same team, leave it standing
    movzx ecx, word [esi+0xD2]
    cmp ecx, 128
    jae sb_next
    movzx ecx, byte [ecx+BLDCLASST]
    cmp ecx, [S_CLASS]
    jne sb_next
    movzx eax, word [esi+0xEE]
    sub eax, [S_TX]
    imul eax, eax
    movzx ecx, word [esi+0xF0]
    sub ecx, [S_TY]
    imul ecx, ecx
    add eax, ecx
    cmp eax, [S_BESTD]
    jge sb_next
    mov [S_BESTD], eax
    mov [S_BEST], edi
sb_next:
    inc edi
    cmp edi, MAXBLD
    jl sb_loop
    mov eax, [S_BEST]
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
]],

scan_wall_code = [[
; nearest wall tile within [S_R] tiles, at least [S_WMIN2] away -> eax = 1/0
scanWall:
    push ebx
    push esi
    push edi
    push ebp
    mov eax, [S_R2]
    mov [S_BESTD], eax
    mov dword [S_BEST], 0
    mov esi, [S_TY]
    sub esi, [S_R]
sw_yloop:
    mov eax, [S_TY]
    add eax, [S_R]
    cmp esi, eax
    jg sw_done
    cmp esi, 0
    jl sw_ynext
    cmp esi, 0x18F
    jg sw_done
    mov eax, esi
    lea eax, [eax+eax*2]
    mov ebp, [eax*4+TILEROWS]
    mov edi, [S_TX]
    sub edi, [S_R]
sw_xloop:
    mov eax, [S_TX]
    add eax, [S_R]
    cmp edi, eax
    jg sw_ynext
    cmp edi, 0
    jl sw_xnext
    cmp edi, 0x18F
    jg sw_ynext
    mov eax, edi
    sub eax, [S_TX]
    imul eax, eax
    mov ecx, esi
    sub ecx, [S_TY]
    imul ecx, ecx
    add eax, ecx
    cmp eax, [S_BESTD]
    jge sw_xnext
    cmp eax, [S_WMIN2]
    jl sw_xnext
    mov ecx, ebp
    add ecx, edi
    test dword [ecx*4+TILEFLAGS], 0x100
    jz sw_xnext
    mov [S_BESTD], eax
    mov [S_WX], edi
    mov [S_WY], esi
    mov dword [S_BEST], 1
sw_xnext:
    inc edi
    jmp sw_xloop
sw_ynext:
    inc esi
    jmp sw_yloop
sw_done:
    mov eax, [S_BEST]
    pop ebp
    pop edi
    pop esi
    pop ebx
    ret
]],

-- Per-unit, per-tick hook inside the unit update loop.
-- Drives units that are configured with an interval, whether or not the game
-- would ever let them shoot on their own.
-- On entry edx = current unit id, esi = unit array base - 0x614.
identity_code = [[
resetUnit:
    pushad
    ; Slot IDs are reused. Track UID, owner and type, resetting only this slot.
    mov ecx, [edx+UNITARRAY+0x98]
    mov ebx, [edx+UNITARRAY+0x8E]
    and ebx, 0xFFFF
    movzx edi, word [edx+UNITARRAY+0x96]
    shl edi, 16
    or ebx, edi
    cmp ecx, [UIDT+eax*4]
    jne t_newunit
    cmp ebx, [IDENTITYT+eax*4]
    je t_identityok
t_newunit:
    mov [UIDT+eax*4], ecx
    mov [IDENTITYT+eax*4], ebx
    mov dword [COOLDOWNT+eax*4], 0
    mov dword [MOVECDT+eax*4], 0
    mov dword [PENDINGT+eax*4], 0
    mov dword [PENDCDT+eax*4], 0
    mov dword [SYNCWAITT+eax*4], 0
    movzx ecx, word [edx+UNITARRAY+0xB6]
    shl ecx, 16
    movzx ebx, word [edx+UNITARRAY+0xB8]
    or ecx, ebx
    mov [LASTPOST+eax*4], ecx
t_identityok:
    popad
    ret
]],

-- Shared scheduled-volley driver. The tick loop or a native release event
-- supplies S_ID, S_PROFILE, S_INTV and S_ONESHOT; all registers are preserved.
automatic_code = [[
automaticVolley:
    pushad
    mov dword [S_FIRED], 0

t_try:
    cmp dword [NATIVECYCLET+edx*4], 0
    jne t_synced                 ; native release already supplies exact timing
    push edx
    push edx
    push dword [S_ID]
    call SYNCREADY
    add esp, 8
    pop edx
    test eax, eax
    jz t_syncwait
t_synced:
    mov eax, [S_ID]
    push edx
    push eax
    call PICKTARGET
    add esp, 8
    test eax, eax
    jz t_failed
    cmp dword [S_ATTACHED], 0
    je t_notboarded
    mov edx, [S_PROFILE]
    cmp dword [ATTBOARDT+edx*4], 0
    je t_notboarded
    mov ecx, [ATTBR2T+edx*4]
    mov [S_BR2], ecx
    push eax
    call ISBOARDED
    mov ecx, eax
    pop eax
    test ecx, ecx
    jnz t_failed                  ; restore the aim even when boarding blocks fire
t_notboarded:
    mov [S_MODE], eax             ; 1 = aimed at a unit, 2 = at a wall or building
    cmp eax, 2
    jne t_shoot
    mov eax, [CURUNIT]
    push eax
    mov ecx, UNITSTATE
    call ACQUIRE
    test eax, eax
    jz t_failed
t_shoot:
    mov dword [S_EXPLICIT], 1
    mov eax, [S_ID]
    mov edx, [S_PROFILE]
    mov esi, [S_UNITPTR]
    mov ecx, [HEIGHTT+edx*4]
    mov [S_HEIGHT], ecx
    mov ecx, [MULTIT+edx*4]
    cmp dword [S_MODE], 1
    je t_multiready
    xor ecx, ecx
t_multiready:
    mov [S_MULTI], ecx
    mov ecx, [INACCT+edx*4]
    mov [S_INACC], ecx
    call CHOOSEAMMO
    push dword [SPREADT+edx*4]
    ; how many projectiles leave right now
    mov ecx, 1
    cmp dword [S_ONESHOT], 0
    jne t_count                   ; a staggered one: exactly one
    mov ecx, [S_VOLLEYCOUNT]
    cmp ecx, 1
    jge t_cntok
    mov ecx, 1
t_cntok:
    cmp dword [STAGMAXT+edx*4], 0
    je t_count                    ; not staggering: the whole volley at once
    mov ecx, 1                    ; staggering: one now, the rest queued below
t_count:
    push ecx
    movsx ecx, word [esi+0xC2]
    add ecx, 30
    push ecx
    movsx ecx, word [esi+0xC0]
    push ecx
    movsx ecx, word [esi+0xBE]
    push ecx
    push dword [S_PROJ]
    mov eax, [S_ID]
    push eax
    call VOLLEY
    add esp, 28
    mov dword [S_FIRED], 1
    ; VOLLEY does not preserve eax/ecx/edx, so everything below reloads.
    cmp dword [S_ONESHOT], 0
    jne t_pendingfired
    mov eax, [S_ID]
    mov ecx, [S_INTV]
    mov [COOLDOWNT+eax*4], ecx
    mov edx, [S_PROFILE]
    cmp dword [STAGMAXT+edx*4], 0
    je t_afterqueue
    mov ecx, [S_VOLLEYCOUNT]
    dec ecx
    cmp ecx, 0
    jle t_afterqueue
    mov [PENDINGT+eax*4], ecx     ; queue the rest of the volley
    push edx
    push eax
    call SETSTAGGER
    add esp, 8
    jmp t_afterqueue
t_pendingfired:
    mov eax, [S_ID]
    dec dword [PENDINGT+eax*4]
    mov edx, [S_PROFILE]
    push edx
    push eax
    call SETSTAGGER
    add esp, 8
t_afterqueue:
    call RESTORETARGET
    jmp t_reset
t_failed:
    call RESTORETARGET
t_retry:
    cmp dword [S_ONESHOT], 0
    jne t_pendingretry
    ; Nothing to shoot at. Look again soon rather than sitting out the whole
    ; interval, otherwise a long interval means a unit almost never notices
    ; an enemy that walks past between two checks.
    mov eax, [S_ID]
    mov edx, [S_PROFILE]
    mov ecx, RETRYTICKS
    cmp dword [PRELOADT+edx*4], 0
    je t_retrycap
    mov ecx, [PRELPOLLT+edx*4]    ; loaded and waiting: look again sooner
t_retrycap:
    cmp ecx, [S_INTV]
    jle t_setcd
    mov ecx, [S_INTV]
t_setcd:
    mov [COOLDOWNT+eax*4], ecx
    jmp t_reset
t_pendingretry:
    mov eax, [S_ID]
    mov dword [PENDCDT+eax*4], RETRYTICKS
    jmp t_reset
t_syncwait:
    mov eax, [S_ID]
    cmp dword [S_ONESHOT], 0
    je t_syncmain
    mov dword [PENDCDT+eax*4], 1
    jmp t_reset
t_syncmain:
    mov dword [COOLDOWNT+eax*4], 1
t_reset:
    ; Put the loop cursor back exactly as we found it, in case anything we
    ; called moved it along.
    mov eax, [S_ID]
    mov [CURUNIT], eax
    jmp av_done
av_done:
    popad
    ret
]],

tick_hook_code = [[
tickHook:
    pushad
    mov eax, [CURUNIT]
    cmp eax, 1
    jl t_done
    cmp eax, MAXUNITS
    jge t_done
    mov dword [NATIVEINTT+eax*4], -1
    mov dword [NATIVEBLOCKT+eax*4], 1
    mov dword [NATIVESEENT+eax*4], 0
    mov edx, eax
    imul edx, edx, 0x490
    push eax
    push eax
    call PROFILE
    add esp, 4
    mov ecx, eax
    mov [S_PROFILE], eax
    pop eax
    cmp ecx, MAXPROFILES
    jae t_done
    cmp dword [INTERVALT+ecx*4], 0
    je t_done
    cmp word [edx+UNITARRAY+0x8C], 2
    jne t_done
    cmp dword [edx+UNITARRAY+0x3C8], 0
    jle t_done
    cmp word [edx+UNITARRAY+0x2A0], 0
    jne t_done
    movzx ecx, word [edx+UNITARRAY+0x96]
    test ecx, ecx
    jz t_done
    cmp ecx, 8
    ja t_done
    call RESETUNIT
    mov edx, [S_PROFILE]
    cmp edx, MAXPROFILES
    jae t_done
    cmp dword [AIONLYT+edx*4], 0
    je t_notaionly
    push edx
    push eax
    push eax
    call ISAIOWNED
    add esp, 4
    mov ecx, eax
    pop eax
    pop edx
    test ecx, ecx
    jz t_done                     ; the player's own unit: leave it be
t_notaionly:
    mov ebx, [INTERVALT+edx*4]
    test ebx, ebx
    jz t_done
    mov [S_ID], eax               ; the called game code is free to clobber
                                  ; registers, so keep what we need in memory
    push edx
    push edx
    push eax
    call CHOOSEINTERVAL
    add esp, 8
    pop edx
    mov ebx, eax
    mov eax, [S_ID]
    mov [NATIVEINTT+eax*4], ebx
    test ebx, ebx
    jz t_done                     ; 0 means "do not shoot in this state"
    mov [S_INTV], ebx
    push edx
    push edx
    push eax
    call CREWOK
    add esp, 8
    pop edx
    test eax, eax
    mov eax, [S_ID]
    jz t_done
t_crewed:
    mov dword [NATIVEBLOCKT+eax*4], 0
    cmp dword [NATIVECYCLET+edx*4], 0
    je t_cooldown
    cmp dword [SYNCWAITT+eax*4], 0
    jle t_cooldown
    dec dword [SYNCWAITT+eax*4]
t_cooldown:
    ; The interval measures time between volley starts. It also advances while
    ; a staggered volley is pending; volleys themselves never overlap.
    mov ecx, [COOLDOWNT+eax*4]
    test ecx, ecx
    jle t_cdelapsed
    dec ecx
    mov [COOLDOWNT+eax*4], ecx
t_cdelapsed:
    ; Prepare the next reload even during a long staggered volley. The release
    ; gate still waits for both the interval and all queued projectiles.
    cmp dword [NATIVECYCLET+edx*4], 0
    je t_pendingcheck
    call NATIVEIDLE
t_pendingcheck:
    ; A staggered volley leaves one projectile at a time. If this unit still owes
    ; some, they take priority over starting a new volley.
    cmp dword [PENDINGT+eax*4], 0
    je t_maincd
    mov ecx, [PENDCDT+eax*4]
    dec ecx
    mov [PENDCDT+eax*4], ecx
    cmp ecx, 0
    jg t_done
    mov dword [S_ONESHOT], 1
    mov eax, [S_ID]
    mov edx, [S_PROFILE]
    jmp t_try
t_maincd:
    cmp dword [NATIVECYCLET+edx*4], 0
    jne t_done
    mov ecx, [COOLDOWNT+eax*4]
    cmp ecx, 0
    jg t_done
    mov dword [S_ONESHOT], 0
t_try:
    call AUTOVOLLEY
    jmp t_done

t_done:
    popad
    add edx, 1
    mov [esi], edx
    jmp RESUME
]],

}
