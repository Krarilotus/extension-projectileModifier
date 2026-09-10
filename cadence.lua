-- Native-animation cadence: reload during the interval and hold at release.
local M = {}
local native_crews = require('constants').native_reload_crews

function M.required(config)
    for name in pairs(native_crews) do
        local cfg = config.units[name] or {}
        local wall = cfg.on_fortification or {}
        if (cfg.interval and cfg.sync_to_animation ~= false)
            or (wall.interval and wall.sync_to_animation ~= false) then return true end
    end
    return false
end

function M.resolve(locate)
    local result = {}
    for _, item in ipairs({
        {39, '80 BA ? ? ? ? 17 0F 85', 2, 23},
        {40, '80 BA ? ? ? ? 1B 0F 85', 2, 27},
        {41, '80 BA ? ? ? ? 16 75', 2, 22},
        {61, '80 BA ? ? ? ? 0C 75 65', 2, 12},
        {77, '0F BE 80 ? ? ? ? 3B C5 89 86 ? ? ? ? 7E 4A', 3, 13},
    }) do
        local address = locate(item[2])
        local script = core.readInteger(address + item[3])
        assert(script >= 0x400000 and script < 0x4000000, 'invalid native release script')
        local found
        for index = 0, 39 do
            if core.readByte(script + index) == item[4] then found = index; break end
        end
        assert(found and found > 0, 'unsupported native release script')
        result[item[1]] = found
    end
    return result
end

-- Tick cached interval/crew eligibility is used by the later animation pass.
-- This prevents movement hysteresis from advancing twice in one simulation tick.
M.release_code = [[
nativeRelease:
    pushad
    mov ebp, esp
    mov eax, [ebp+36]
    mov edx, [ebp+40]
    mov ecx, eax
    imul ecx, ecx, 0x490
    mov ebx, [NATIVECYCLET+edx*4]
    cmp ebx, [ecx+UNITARRAY+0x2B0]
    jne nr_done
    cmp dword [ecx+UNITARRAY+0x50], 0
    je nr_done
    cmp dword [NATIVESEENT+eax*4], 0
    jne nr_done
    mov dword [NATIVESEENT+eax*4], 1
    cmp dword [NATIVEBLOCKT+eax*4], 0
    jne nr_refund
    cmp dword [COOLDOWNT+eax*4], 0
    jg nr_refund
    cmp dword [PENDINGT+eax*4], 0
    jg nr_refund
    mov ecx, [NATIVEINTT+eax*4]
    cmp ecx, 0
    jle nr_refund
    mov [S_ID], eax
    mov [S_PROFILE], edx
    mov [S_INTV], ecx
    mov dword [S_ONESHOT], 0
    push eax
    call CHECKATTACHED
    add esp, 4
    mov edx, [S_PROFILE]
    call AUTOVOLLEY
    cmp dword [S_FIRED], 0
    jne nr_done
nr_refund:
    ; The native catapult/trebuchet charged a stone before reaching dispatch.
    ; A target can disappear between the hold check and dispatch. Refund that
    ; charge if no configured shot was released. Mangonels have no such charge.
    mov eax, [ebp+36]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    movzx ecx, word [eax+0x8E]
    cmp ecx, 39
    je nr_stone
    cmp ecx, 40
    jne nr_done
nr_stone:
    inc word [eax+0x362]
nr_done:
    popad
    ret
]]

-- Start native reload only from idle, preserving move/attack/cow orders already
-- in progress. Target picking temporarily saves/restores the native order fields.
M.idle_code = [[
nativeIdle:
    pushad
    mov eax, [S_ID]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    cmp word [eax+0x2C0], 0
    jne ni_done
    cmp word [eax+0x3B0], 0
    jne ni_done
    push dword [S_PROFILE]
    push dword [S_ID]
    call NATIVETARGET
    add esp, 8
    test eax, eax
    jz ni_done
    mov eax, [S_ID]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    mov word [eax+0x2C0], 2
    mov dword [eax+0x2B0], 0
ni_done:
    popad
    ret
]]

-- Failed target scans use the existing saved per-unit wait counter. Native
-- cadence does not use the legacy animation wait, so the two never overlap.
M.target_code = [[
nativeTarget:
    pushad
    mov ebp, esp
    mov ebx, [ebp+36]
    xor eax, eax
    cmp dword [SYNCWAITT+ebx*4], 0
    jg nt_done
    push dword [ebp+40]
    push ebx
    call PICKTARGET
    add esp, 8
    push eax
    call RESTORETARGET
    pop eax
    test eax, eax
    jnz nt_done
    mov edx, [ebp+40]
    mov ecx, RETRYTICKS
    cmp dword [PRELOADT+edx*4], 0
    je nt_cap
    mov ecx, [PRELPOLLT+edx*4]
nt_cap:
    cmp ecx, [NATIVEINTT+ebx*4]
    jle nt_wait
    mov ecx, [NATIVEINTT+ebx*4]
nt_wait:
    mov [SYNCWAITT+ebx*4], ecx
nt_done:
    mov [ebp+28], eax
    popad
    ret
]]

M.configured_hook = [[
configuredAnimationHold:
    pushfd
    pushad
    mov ebx, [CURUNIT]
    cmp ebx, 1
    jl ca_pass
    cmp ebx, MAXUNITS
    jae ca_pass
    cmp dword [NATIVEINTT+ebx*4], -1
    je ca_pass
    push ebx
    call PROFILE
    add esp, 4
    cmp eax, MAXPROFILES
    jae ca_pass
    mov edx, eax
    mov ecx, [NATIVECYCLET+eax*4]
    test ecx, ecx
    jz ca_pass
    push dword [NATIVEBLOCKT+ebx*4]
    push dword [COOLDOWNT+ebx*4]
    push ecx
    push ebx
    call SHOULDHOLD
    add esp, 16
    test eax, eax
    jnz ca_hold
    ; If the cooldown has elapsed, check whether this is the release transition
    ; using a synthetic block, then validate the selected target before native
    ; code can consume ammunition.
    mov eax, [CURUNIT]
    push eax
    call PROFILE
    add esp, 4
    mov ecx, [NATIVECYCLET+eax*4]
    push 1
    push 0
    push ecx
    push dword [CURUNIT]
    call SHOULDHOLD
    add esp, 16
    test eax, eax
    jz ca_pass
    cmp dword [PENDINGT+ebx*4], 0
    jg ca_hold
    push dword [CURUNIT]
    call PROFILE
    add esp, 4
    push eax
    push dword [CURUNIT]
    call NATIVETARGET
    add esp, 8
    test eax, eax
    jz ca_hold
ca_pass:
    popad
    popfd
    add dword [eax+esi+0x654], ebx
    jmp RESUME
ca_hold:
    popad
    popfd
    mov dword [eax+esi+0x664], 0
    mov ecx, [CURUNIT]
    jmp ANIMATIONDONE
]]

-- shouldHold(unitID, releaseCycle, remaining, blocked) -> bool
-- remaining is a shot-to-shot cooldown, decremented once per simulation tick.
-- blocked covers hold-fire/crew/target/queued-volley gating. Caller has resolved
-- a supported native attack profile. Return true only at the transition INTO
-- the release frame. Let reload/wind-up proceed until that point; do not freeze
-- movement, the recoil after a shot, or an unconfigured native cow order.
M.hold_code = [[
shouldHold:
    push ebx
    mov eax, [esp+8]
    cmp eax, 1
    jl nh_no
    cmp eax, MAXUNITS
    jae nh_no
    imul eax, eax, 0x490
    add eax, UNITARRAY
    cmp word [eax+0x3B0], 0
    jne nh_no
    cmp word [eax+0x2C0], 4
    jne nh_no
    mov ecx, [esp+12]
    cmp ecx, 1
    jl nh_no
    dec ecx
    cmp ecx, [eax+0x2B0]
    jne nh_no
    mov ecx, [eax+0x40]
    inc ecx
    mov edx, [eax+0x3C]
    add edx, [eax+0x44]
    cmp ecx, edx
    jle nh_no
    cmp dword [esp+20], 0
    jne nh_yes
    cmp dword [esp+16], 0
    jle nh_no
nh_yes:
    mov eax, 1
    pop ebx
    ret
nh_no:
    xor eax, eax
    pop ebx
    ret
]]

-- At the original animation ticker increment: EAX=id*stride, ESI=UnitState,
-- EBX=1. The caller supplies already-resolved RELEASECYCLE and gating arrays.
M.animation_hook = [[
animationHold:
    pushfd
    pushad
    mov eax, [CURUNIT]
    push dword [BLOCKEDT+eax*4]
    push dword [COOLDOWNT+eax*4]
    push RELEASECYCLE
    push eax
    call SHOULDHOLD
    add esp, 16
    test eax, eax
    jz ah_pass
    popad
    popfd
    mov dword [eax+esi+0x664], 0
    mov ecx, [CURUNIT]
    jmp ANIMATIONDONE
ah_pass:
    popad
    popfd
    add dword [eax+esi+0x654], ebx
    jmp RESUME
]]
return M
