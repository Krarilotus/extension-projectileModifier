-- Native-animation cadence: preserve native cycles and delay at safe poses.
local M = {}
local constants = require('constants')
local configuration = require('configuration')
local native_crews = constants.native_reload_crews

-- Raw unit types, independent of the base/fortification profile selection.
M.attack_states = {[6]=10, [22]=6, [23]=6, [39]=4, [40]=4, [41]=4,
    [61]=4, [70]=6, [72]=6, [76]=6, [77]=4}
M.start_states = {[6]=10, [22]=4, [23]=4, [39]=8, [40]=8, [41]=8,
    [61]=8, [70]=4, [72]=4, [74]=4, [76]=4, [77]=8}

local function native_profile(profile)
    return profile.interval and profile.sync_to_animation ~= false
end

local function enabled(config, name)
    if config == nil then return true end
    return configuration.any_profile(config.units[name] or {}, native_profile)
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

function M.resolve_catapult_rest(locate, release_cycle)
    if not release_cycle then return nil end
    -- Final native reload entry: engine pose 13 (arm down), engineer pose 41.
    -- The old release gate waited at firing pose 22, with the arm raised.
    local site = locate('8B 1D ? ? ? ? 8B C3 69 C0 90 04 00 00 8B 88 ? ? ? ? 0F BE 89 ? ? ? ? 3B CD 89 88 ? ? ? ? 7F 17 5F 5E') + 8
    local script = core.readInteger(site + 15)
    assert(script >= 0x400000 and script < 0x4000000, 'invalid catapult reload script')
    local finish
    for index = 1, 39 do
        if core.readByte(script + index) == 0 then finish = index; break end
    end
    assert(core.readByte(site + 0x4B) == 0x0F and core.readByte(site + 0x4C) == 0xBE
        and core.readByte(site + 0x4D) == 0x8A, 'unsupported catapult engineer script')
    local crew = core.readInteger(site + 0x4E)
    assert(crew >= 0x400000 and crew < 0x4000000
        and finish and finish > 1 and core.readByte(script + finish - 1) == 13
        and core.readByte(crew + finish - 1) == 41 and core.readByte(crew + finish) == 0,
        'unsupported catapult lowered pose')
    local speed = site - 0x8C
    local attack = speed + 14 + core.readInteger(speed + 10)
    assert(attack >= 0x400000 and attack < 0x700000
        and core.readByte(speed) == 0xB9 and core.readInteger(speed + 1) == 2
        and core.readInteger(speed + 5) == 0x0FC13B66
        and core.readByte(speed + 9) == 0x85
        and core.readInteger(attack) == 0x00043D66
        and core.readSmallInteger(attack + 10) % 65536 == 0x8E89
        and core.readInteger(attack + 12) == core.readInteger(speed + 16),
        'unsupported catapult firing speed')
    return {cycle=finish-1, lead=release_cycle * (core.readInteger(speed + 1) + 1)}
end

function M.resolve_trebuchet_rest(locate, release_cycle)
    if not release_cycle then return nil end
    -- The trebuchet's firing phase already starts its swing. The loaded pose
    -- is the LAST reload-script entry, before state 2 advances to state 4.
    local site = locate('69 DB 90 04 00 00 8B 83 ? ? ? ? 0F BE 80 ? ? ? ? 3B C2 89 83 ? ? ? ? 7F 1A 5F 5E')
    local script = core.readInteger(site + 15)
    assert(script >= 0x400000 and script < 0x4000000, 'invalid trebuchet reload script')
    local finish
    for index = 1, 99 do
        if core.readByte(script + index) == 0 then finish = index; break end
    end
    assert(core.readByte(site + 0x65) == 0x0F and core.readByte(site + 0x66) == 0xBE
        and core.readByte(site + 0x67) == 0x88, 'unsupported trebuchet body script')
    local body = core.readInteger(site + 0x68)
    assert(body >= 0x400000 and body < 0x4000000, 'invalid trebuchet body script')
    assert(finish and finish > 1 and core.readByte(body + finish - 1) == 23
        and core.readByte(body + finish) == 0,
        'unsupported trebuchet loaded pose')
    -- ECX=2 is loaded before the state dispatch and written to the firing
    -- phase's frame delay. Validate that path before deriving its lead time.
    local speed = locate('B9 ? ? ? ? 66 3B C1 0F 85 ? ? ? ? C7 86 ? ? ? ? 05 00 00 00 89 96 ? ? ? ? 66 89 96 ? ? ? ?')
    local attack = speed + 14 + core.readInteger(speed + 10)
    assert(attack >= 0x400000 and attack < 0x700000
        and core.readInteger(speed + 1) == 2
        and core.readInteger(attack) == 0x00043D66
        and core.readSmallInteger(attack + 10) % 65536 == 0x8E89
        and core.readInteger(attack + 12) == core.readInteger(speed + 16),
        'unsupported trebuchet firing speed')
    return {cycle=finish-1, lead=release_cycle * (core.readInteger(speed + 1) + 1)}
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
    push dword [S_ID]
    call MANUALORDER
    add esp, 4
    test eax, eax
    jz nr_search
    mov eax, [ebp+44]            ; native code already acquired and charged this shot
nr_search:
    push eax                    ; zero retains automatic AI/search behavior
    mov edx, [S_PROFILE]
    call AUTOVOLLEY
    add esp, 4
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

-- Enter the native aiming state from idle. Siege state 8 owns turning and
-- enters reload only after alignment; starting at reload (2) skips rotation.
-- Preserve movement/cow states already in progress.
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
    mov ecx, [S_ID]
    cmp dword [PENDINGT+ecx*4], 0
    je ni_acquire
    push ecx
    call MANUALORDER
    add esp, 4
    test eax, eax
    jnz ni_start                 ; queued native shots already own their aim
ni_acquire:
    push dword [S_PROFILE]
    push dword [S_ID]
    call NATIVETARGET
    add esp, 8
    test eax, eax
    jz ni_done
ni_start:
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
    push ebx
    call MANUALORDER
    add esp, 4
    mov edi, eax               ; snapshot before an automatic scan changes order
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
    cmp dword [NATIVESTARTT+ecx*4], 8
    je nt_siege
    cmp dword [NATIVESTARTT+ecx*4], 4
    jne nt_restore
    ; Configured infantry targets must reach the native wind-up and LOS/UID
    ; checks. Otherwise a stale prior target can discard a valid loaded shot.
    cmp eax, 2
    je nt_ground
    mov ecx, [S_UNITPTR]
    mov word [ecx+0x39C], 3
    jmp nt_done
nt_siege:
    cmp eax, 2
    jne nt_siegeunit
    test edi, edi
    jnz nt_done                 ; PICKTARGET already acquired this human order
    jmp nt_ground               ; newly selected automatic building/wall target
nt_siegeunit:
    ; A configured automatic unit target supplies the same tile fields used by
    ; the original siege aiming state. Retain the selected UID as for infantry.
    ; Human explicit orders use mode 2 and never take this path.
    mov ecx, [S_UNITPTR]
    movsx edx, word [ecx+0xBE]
    sar edx, 3
    mov word [ecx+0x3E8], dx
    movsx edx, word [ecx+0xC0]
    sar edx, 3
    mov word [ecx+0x3EA], dx
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
    ; At a loaded/release transition, use a synthetic block to validate the
    ; selected target before native code starts the swing or consumes ammunition.
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
-- a supported native attack profile. Catapults/trebuchets wait at the reload pose
-- and start the swing early enough to release on time. Retain the release gate
-- for late eligibility changes. Do not freeze movement, recoil or native cows.
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
    xor ebx, ebx               ; remaining ticks allowed before this transition
    cmp ecx, 39
    jne nh_trebuchet
    cmp word [eax+0x2C0], 2
    jne nh_attack
    cmp dword [eax+0x2B0], CATRESTCYCLE
    jne nh_no
    mov ebx, CATRELEASELEAD
    jmp nh_transition
nh_trebuchet:
    cmp ecx, 40
    jne nh_attack
    cmp word [eax+0x2C0], 2
    jne nh_attack
    cmp dword [eax+0x2B0], TREBRESTCYCLE
    jne nh_no
    mov ebx, TREBRELEASELEAD
    jmp nh_transition
nh_attack:
    mov ecx, [NATIVEATTACKT+ecx*4]
    cmp word [eax+0x2C0], cx
    jne nh_no
    mov ecx, [esp+12]
    cmp ecx, 1
    jl nh_no
    dec ecx
    cmp ecx, [eax+0x2B0]
    jne nh_no
nh_transition:
    mov ecx, [eax+0x40]
    inc ecx
    mov edx, [eax+0x3C]
    add edx, [eax+0x44]
    cmp ecx, edx
    jle nh_no
    cmp dword [esp+20], 0
    jne nh_yes
    cmp dword [esp+16], ebx
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
