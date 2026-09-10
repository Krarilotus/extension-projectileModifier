-- Native-animation cadence: reload during the interval and hold at release.
local M = {}
local constants = require('constants')
local native_crews = constants.native_reload_crews

-- Raw unit types, independent of the base/fortification profile selection.
M.attack_states = {[6]=10, [22]=6, [23]=6, [39]=4, [40]=4, [41]=4,
    [61]=4, [70]=6, [72]=6, [76]=6, [77]=4}
M.start_states = {[6]=10, [22]=4, [23]=4, [39]=2, [40]=2, [41]=2,
    [61]=2, [70]=4, [72]=4, [74]=4, [76]=4, [77]=2}

local function enabled(config, name)
    if config == nil then return true end
    local cfg = config.units[name] or {}
    local wall = cfg.on_fortification or {}
    for _, rule in ipairs(cfg.near_decorations or {}) do
        for _, profile in ipairs({rule.ground, rule.fortified}) do
            if profile.interval and profile.sync_to_animation ~= false then return true end
        end
    end
    return (cfg.interval and cfg.sync_to_animation ~= false)
        or (wall.interval and wall.sync_to_animation ~= false)
end

function M.required(config)
    for name in pairs(native_crews) do
        if enabled(config, name) then return true end
    end
    return false
end

function M.resolve(locate, config)
    local result = {}
    for _, item in ipairs({
        {6, '0F BE 80 ? ? ? ? 83 C4 08 3B C5 89 86 ? ? ? ? 7E 14', 3, 22},
        {39, '80 BA ? ? ? ? 17 0F 85', 2, 23},
        {40, '80 BA ? ? ? ? 1B 0F 85', 2, 27},
        {41, '80 BA ? ? ? ? 16 75', 2, 22},
        {61, '80 BA ? ? ? ? 0C 75 65', 2, 12},
        {77, '0F BE 80 ? ? ? ? 3B C5 89 86 ? ? ? ? 7E 4A', 3, 13},
        {22, '0F BE 82 ? ? ? ? 85 C0 89 86 ? ? ? ? 7E 6D 0F BF 96 ? ? ? ? 8D 84 C2 79 01 00 00', 3, 6},
        {70, '0F BE 81 ? ? ? ? 83 CA FF 85 C0 89 86 ? ? ? ? 7E 4B', 3, 22},
        {72, '0F BE 81 ? ? ? ? 85 C0 89 86 ? ? ? ? 7E 6D 0F BF 8E ? ? ? ? 8D 84 C1 C1 01 00 00', 3, 12},
        {76, '0F BE 81 ? ? ? ? 85 C0 89 86 ? ? ? ? 7E 14 0F BF 96 ? ? ? ? 8D 84 C2 39 01 00 00', 3, 20},
        {74, '0F BE 89 ? ? ? ? 89 8E ? ? ? ? 8B 8E ? ? ? ? 3B CB', 3, 27},
    }) do
      if enabled(config, constants.unit_names[item[1]]) then
        local address = locate(item[2])
        local script = core.readInteger(address + item[3])
        assert(script >= 0x400000 and script < 0x4000000, 'invalid native release script')
        local found
        -- Script index zero is the phase's initial pose. The animation pass
        -- advances before the first update: slingers release at index 1.
        for index = 1, 39 do
            if core.readByte(script + index) == item[4] then found = index; break end
        end
        assert(found and found > 0, 'unsupported native release script')
        result[item[1]] = found
      end
    end
    -- Crossbows compare the cycle itself, not the rendered frame; all three
    -- elevation scripts share this gate. Resolve its immediate from the code.
    if enabled(config, 'European crossbowman') then
    local crossbow = locate('B9 ? ? ? ? 89 8E ? ? ? ? C7 86 ? ? ? ? 00 00 00 00 0F B7 86 ? ? ? ? 83 CA FF 66 85 C0 75 0F')
    assert(core.readByte(crossbow + 0x78) == 0x39
        and core.readByte(crossbow + 0x79) == 0x8E, 'unsupported crossbow release gate')
    result[23] = core.readInteger(crossbow + 1)
    assert(result[23] == 2, 'unsupported crossbow release cycle')
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

-- Start native reload only from idle, preserving movement/cow states already
-- in progress. Foot shooters need the selected target for their native checks.
M.idle_code = [[
nativeIdle:
    pushad
    mov eax, [S_ID]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    cmp word [eax+0x8E], 74
    je ni_horse
    cmp word [eax+0x2C0], 0
    jne ni_done
    cmp word [eax+0x3B0], 0
    jne ni_done
    jmp ni_target
ni_horse:
    cmp word [eax+0x424], 0
    jne ni_done
    movzx ecx, word [eax+0x2C0]
    cmp ecx, 0
    je ni_target
    cmp ecx, 4
    je ni_target
    cmp ecx, 101
    jne ni_done
ni_target:
    push dword [S_PROFILE]
    push dword [S_ID]
    call NATIVETARGET
    add esp, 8
    test eax, eax
    jz ni_done
    mov eax, [S_ID]
    imul eax, eax, 0x490
    add eax, UNITARRAY
    cmp word [eax+0x8E], 74
    jne ni_ordinary
    mov word [eax+0x424], 4
    cmp word [eax+0x2C0], 0
    jne ni_done
ni_ordinary:
    movzx ecx, word [eax+0x8E]
    mov ecx, [NATIVESTARTT+ecx*4]
    mov word [eax+0x2C0], cx
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
    test eax, eax
    jz nt_restore
    mov ecx, [S_UNITPTR]
    movzx ecx, word [ecx+0x8E]
    cmp ecx, 6
    je nt_hunter
    cmp dword [NATIVESTARTT+ecx*4], 4
    jne nt_restore
    ; Configured infantry targets must reach the native wind-up and LOS/UID
    ; checks. Otherwise a stale prior target can discard a valid loaded shot.
    cmp eax, 2
    je nt_ground
    mov ecx, [S_UNITPTR]
    mov word [ecx+0x39C], 3
    jmp nt_done
nt_ground:
    push ebx
    mov ecx, UNITSTATE
    call ACQUIRE
    test eax, eax
    jnz nt_done
    jmp nt_restore
nt_hunter:
    ; Turn toward the temporary aim without overwriting the hunter's work order.
    ; The native tile-facing helper also respects the current camera rotation.
    cmp eax, 2
    jne nt_hunterface
    push ebx
    mov ecx, UNITSTATE
    call ACQUIRE
    test eax, eax
    jz nt_restore
    mov eax, 2
nt_hunterface:
    push eax
    mov ecx, [S_UNITPTR]
    movsx edx, word [ecx+0xC0]
    sar edx, 3
    push edx
    movsx edx, word [ecx+0xBE]
    sar edx, 3
    push edx
    push ebx
    mov ecx, UNITSTATE
    call HUNTERFACE
    pop eax
nt_restore:
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
    imul eax, ebx, 0x490
    cmp word [eax+UNITARRAY+0x8E], 74
    je ca_pass                   ; bow routine owns a separate temporary clock
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
    movzx ecx, word [eax+0x8E]
    cmp ecx, MAXTYPES
    jae nh_no
    mov ecx, [NATIVEATTACKT+ecx*4]
    cmp word [eax+0x2C0], cx
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
