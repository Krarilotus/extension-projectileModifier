-- map-extensions owns save/load and new-world initialization. Only simulation
-- state belongs here; configuration, code and temporary targeting scratch do not.
--
-- Saved formats (`format` entry):
--   1-4  test builds 1.3.2-1.7.x. Their block layouts differ from today's; the
--        world keeps its units and this module's timers start fresh.
--   5    1.8.x up to 1.8.19. No unit capacity entry; it is derived from the
--        per-unit blocks, which must all agree.
--   6    1.8.20+. Records the unit capacity it was saved with.
-- Any other value is refused, so a newer or damaged save is never guessed at.
-- Within formats 5 and 6 every block must be present, have the size its
-- format defines and stay inside its value range; damaged data is refused.
-- Two kinds of difference are defined migrations, not damage:
--   * changed projectile/decoration graphics or a different graphics-slot
--     layout: projectiles in flight take their default look; placed
--     decorations keep their kind by name (format 6 records the names) and
--     get the new graphics. A decoration whose definition was removed becomes
--     an ordinary brazier. In both cases the game's own entity record is set
--     back to the native graphics ID it would have without this module.
--     Format 5 has no names: its placed decorations must keep their
--     definitions (refused otherwise, as before);
--   * a different unit capacity (Crusader 2500, Extreme 10000, e.g. a map made
--     in the other edition): per-unit blocks are widened with empty slots, or
--     narrowed only when the dropped slots are empty.
local M = {}
local FORMAT = '6'
local LEGACY_FORMATS = {['1']=true, ['2']=true, ['3']=true, ['4']=true}
local CAPACITIES = {[2500]=true, [10000]=true}
local UNIT_BYTES = 4

local function canonical(value)
    if type(value) ~= 'table' then return type(value) .. ':' .. tostring(value) end
    local keys, parts = {}, {}
    for key in pairs(value) do keys[#keys+1] = key end
    table.sort(keys, function(a,b) return tostring(a) < tostring(b) end)
    for _, key in ipairs(keys) do parts[#parts+1] = canonical(key) .. '=' .. canonical(value[key]) end
    return '{' .. table.concat(parts, ';') .. '}'
end

local function empty(bytes)
    return not bytes:find('[^%z]')
end

local function dword(bytes, index)  -- entry `index` (0-based) of a dword array
    local a, b, c, d = bytes:byte(index * 4 + 1, index * 4 + 4)
    return a + b*256 + c*65536 + d*16777216
end

local function dwords(values, count)
    local parts = {}
    for index = 0, count - 1 do parts[#parts+1] = string.pack('<I4', values[index] or 0) end
    return table.concat(parts)
end

-- `id=name;` for every decoration. Names are restricted to
-- lowercase letters, digits, `_` and `-`, so the encoding is unambiguous.
local function encode_names(definitions)
    local ids = {}
    for name, spec in pairs(definitions or {}) do ids[#ids+1] = {spec.id, name} end
    table.sort(ids, function(a, b) return a[1] < b[1] end)
    local parts = {}
    for _, entry in ipairs(ids) do parts[#parts+1] = entry[1] .. '=' .. entry[2] .. ';' end
    return table.concat(parts)
end

local function decode_names(text)
    assert(type(text) == 'string' and text:gsub('%d+=[a-z][a-z0-9_%-]*;', '') == '',
        '[custom-projectiles] invalid saved graphics names')
    local names = {}
    for id, name in text:gmatch('(%d+)=([a-z][a-z0-9_%-]*);') do names[tonumber(id)] = name end
    return names
end

local ENTITIES = 3000  -- native entity array length, both editions
local BRAZIER_GM = 138

-- blocks: {name, address, size, layout} with `units=true` on per-unit blocks
-- (size = capacity * 4). Layout blocks are rebuilt from the current
-- configuration and never restored.
-- looks: {projectile_gm(type) -> native GM, restore(entity, uid, slot, gm)}
-- from init.lua. restore writes `gm` into the game's entity record only if it
-- is still the same entity and still shows the old custom slot.
function M.new(blocks, config, profile_count, rebuild, capacity, looks)
    local gameplay = {units=config.units, projectiles=config.projectiles, decorations=config.decorations}
    if config.projectile_physics then gameplay.projectile_physics = config.projectile_physics end
    -- Load policy is not gameplay identity. Existing saves keep the same
    -- fingerprint when their gameplay fields have not changed.
    local state = {blocks=blocks, allow_config_changes=config.allow_config_changes_on_load ~= false,
        config=canonical(gameplay), capacity=capacity,
        assets=canonical({projectiles=config.projectiles or {}, decorations=config.decorations or {}}),
        decoration_names=encode_names(config.decorations)}
    local decoration_ids = {}
    for name, spec in pairs(config.decorations or {}) do decoration_ids[name] = spec.id end
    for _, block in ipairs(blocks) do
        assert(not block.units or block[3] == capacity * UNIT_BYTES,
            '[custom-projectiles] per-unit save block does not match the unit capacity: ' .. block[1])
    end
    local retained = {seed=true, ['entity-variant']=true, ['entity-uid']=true,
        ['entity-type']=true, ['decoration-variant']=true, ['decoration-uid']=true}
    local limits = {cooldown=60000, movement=20, pending=63, ['pending-cooldown']=60000, ['sync-wait']=60000, profile=(profile_count or 160)-1,
        ['weapon-cycle']=40, ['weapon-tick']=1, ['weapon-phase']=6,
        ['entity-variant']=33, ['entity-type']=255, ['decoration-variant']=33}
    function state:initialize()
        for _, block in ipairs(self.blocks) do
            if not block[4] then core.setMemory(block[2], 0, block[3]) end
        end
        core.writeInteger(self.blocks[1][2], 0x1D872B41)
        if rebuild then rebuild() end
    end
    function state:serialize(handle)
        handle:put('format', FORMAT)
        handle:put('config', self.config)
        handle:put('assets', self.assets)
        handle:put('capacity', tostring(self.capacity))
        handle:put('decoration-names', self.decoration_names)
        for _, block in ipairs(self.blocks) do
            handle:put(block[1] .. '.bin', core.readString(block[2], block[3]))
        end
    end
    -- The unit capacity a format-5/6 save was written with.
    function state:saved_capacity(handle, format, saved)
        if format == FORMAT then
            local value = handle:exists('capacity') and math.tointeger(tonumber(handle:get('capacity')))
            assert(value and CAPACITIES[value], '[custom-projectiles] invalid saved unit capacity')
            return value
        end
        local value
        for i, block in ipairs(self.blocks) do
            if block.units then
                local count = #saved[i] // UNIT_BYTES
                assert(#saved[i] % UNIT_BYTES == 0 and (value == nil or value == count),
                    '[custom-projectiles] invalid saved state: ' .. block[1] .. '.bin')
                value = count
            end
        end
        assert(value and CAPACITIES[value], '[custom-projectiles] invalid saved unit capacity')
        return value
    end
    -- Map Extensions calls this before restoring any extension. Direct restores
    -- use the same validator; no pending state is retained between callbacks.
    function state:validate(handle)
        local present = handle:exists('format')
        if not present and not handle.required then return end
        local format = present and handle:get('format')
        if LEGACY_FORMATS[format] and self.allow_config_changes then
            return {fresh=true, notes={'saved by an older test version (state format ' .. format
                .. '); projectile timers start fresh'}}
        end
        assert(format == '5' or format == FORMAT,
            '[custom-projectiles] unsupported saved state format; start a new match with this version')
        local saved_config = handle:get('config')
        assert(type(saved_config) == 'string' and saved_config:sub(1,1) == '{' and saved_config:sub(-1) == '}',
            '[custom-projectiles] invalid saved projectile configuration')
        local changed = saved_config ~= self.config
        assert(not changed or self.allow_config_changes,
            '[custom-projectiles] saved projectile settings differ; restore the settings used for this save or enable allow_config_changes_on_load')
        local notes = {}
        if changed then
            notes[#notes+1] = 'projectile settings changed since this save; firing timers were reset'
        end
        -- A format-5 save without an asset identity counts as changed graphics.
        local assets_changed = changed and (not handle:exists('assets') or handle:get('assets') ~= self.assets)
        local saved = {}
        for i, block in ipairs(self.blocks) do
            local name = block[1] .. '.bin'
            assert(handle:exists(name), '[custom-projectiles] missing saved state: ' .. name)
            saved[i] = handle:get(name)
            assert(type(saved[i]) == 'string', '[custom-projectiles] invalid saved state: ' .. name)
        end
        local capacity = self:saved_capacity(handle, format, saved)
        -- Strict mode keeps the exact-match rules of earlier versions.
        assert(capacity == self.capacity or self.allow_config_changes,
            '[custom-projectiles] save was made with a different unit limit; enable allow_config_changes_on_load to load it')
        if capacity ~= self.capacity then
            notes[#notes+1] = 'save was made with ' .. capacity .. ' unit slots, this game has '
                .. self.capacity .. '; unit timers were moved to the new limit'
        end
        local pending = {reconfigure=changed, notes=notes}
        for i, block in ipairs(self.blocks) do
            local name = block[1] .. '.bin'
            local bytes = saved[i]
            local size = block.units and capacity * UNIT_BYTES or block[3]
            assert(#bytes == size, '[custom-projectiles] invalid saved state: ' .. name)
            if block[4] then
                -- Graphics-slot layouts are rebuilt from this configuration.
                assert(bytes == core.readString(block[2], block[3]) or self.allow_config_changes,
                    '[custom-projectiles] saved graphics-slot layout differs; restore the same extensions and sprite configuration')
            end
            if limits[block[1]] and not (changed and block[1] == 'profile') then
                for offset = 1, #bytes, 4 do
                    local a,b,c,d = bytes:byte(offset, offset+3)
                    local value = a + b*256 + c*65536 + d*16777216
                    assert(value <= limits[block[1]], '[custom-projectiles] out-of-range saved state: ' .. name)
                end
            end
            if block.units and #bytes > block[3] then
                assert(empty(bytes:sub(block[3] + 1)),
                    '[custom-projectiles] save tracks units beyond this game\'s unit limit: ' .. name)
                bytes = bytes:sub(1, block[3])
            elseif block.units and #bytes < block[3] then
                bytes = bytes .. string.rep('\0', block[3] - #bytes)
            end
            pending[i] = bytes
        end
        self:plan_looks(handle, format, assets_changed, pending)
        return pending
    end
    -- Decide what custom graphics in the saved world become, using only
    -- validated data. Rewrites the pending entity/decoration blocks and lists
    -- the game entity records whose graphics ID must go back to native.
    function state:plan_looks(handle, format, assets_changed, pending)
        local index = {}
        for i, block in ipairs(self.blocks) do index[block[1]] = i end
        local function saved(name) return pending[index[name]] end
        local function current(name)
            local block = self.blocks[index[name]]
            return core.readString(block[2], block[3])
        end
        local fixes = {}
        pending.looks, pending.reset_visuals = fixes, false
        -- Projectiles in flight: a different definition or slot layout means
        -- their saved variant may now be another sprite. They last seconds,
        -- so they take their default look.
        local variants, uids, types = saved('entity-variant'), saved('entity-uid'), saved('entity-type')
        local old_slots = saved('variant-gm')
        if not empty(variants) and (assets_changed or old_slots ~= current('variant-gm')) then
            for entity = 0, ENTITIES - 1 do
                local variant = dword(variants, entity)
                if variant ~= 0 then
                    local gm = looks and looks.projectile_gm(dword(types, entity))
                    local slot = dword(old_slots, variant)
                    if gm and slot ~= 0 then fixes[#fixes+1] = {entity, dword(uids, entity), slot, gm} end
                end
            end
            local zero = string.rep('\0', ENTITIES * 4)
            pending[index['entity-variant']], pending[index['entity-uid']], pending[index['entity-type']] = zero, zero, zero
            pending.notes[#pending.notes+1] = 'custom projectile graphics changed; projectiles in flight use their default look'
            pending.reset_visuals = true
        end
        -- Placed decorations keep their kind by name; their graphics follow
        -- the current definition. A removed definition leaves a brazier.
        local placed, owners = saved('decoration-variant'), saved('decoration-uid')
        local old_decor = saved('decoration-gm')
        local layout_changed = old_decor ~= current('decoration-gm')
        if empty(placed) or not (assets_changed or layout_changed) then return end
        local map = {}
        if assets_changed then
            assert(format == FORMAT and handle:exists('decoration-names'),
                '[custom-projectiles] placed custom decorations changed in a save from an older version; restore their definitions, or load and save once with this version before editing them')
            for id, name in pairs(decode_names(handle:get('decoration-names'))) do map[id] = decoration_ids[name] or 0 end
        else
            for id = 1, 33 do map[id] = id end
        end
        local variants_out, owners_out, removed = {}, {}, 0
        for entity = 0, ENTITIES - 1 do
            local variant = dword(placed, entity)
            if variant ~= 0 then
                local uid, new = dword(owners, entity), map[variant] or 0
                local slot = dword(old_decor, variant)
                if slot ~= 0 and slot ~= BRAZIER_GM then fixes[#fixes+1] = {entity, uid, slot, BRAZIER_GM} end
                if new == 0 then removed = removed + 1 else variants_out[entity], owners_out[entity] = new, uid end
            end
        end
        pending[index['decoration-variant']] = dwords(variants_out, ENTITIES)
        pending[index['decoration-uid']] = dwords(owners_out, ENTITIES)
        pending.notes[#pending.notes+1] = 'custom decoration graphics changed; placed decorations use their current definition'
        if removed > 0 then
            pending.notes[#pending.notes+1] = removed .. ' placed decoration(s) no longer defined; they are ordinary braziers now'
        end
        pending.reset_visuals = true
    end
    function state:deserialize(handle)
        local pending = self:validate(handle)
        if not pending then self:initialize(); return end
        for _, note in ipairs(pending.notes) do log(WARNING, '[custom-projectiles] ' .. note) end
        if pending.fresh then self:initialize(); return end
        for i, block in ipairs(self.blocks) do
            if block[4] then
                -- rebuilt by rebuild() below
            elseif pending.reconfigure and not retained[block[1]] then
                core.setMemory(block[2], 0, block[3])
            else
                local bytes = {}
                for j = 1, #pending[i] do bytes[j] = pending[i]:byte(j) end
                core.writeBytes(block[2], bytes)
            end
        end
        if #pending.looks > 0 then
            if looks and looks.restore then
                for _, fix in ipairs(pending.looks) do looks.restore(fix[1], fix[2], fix[3], fix[4]) end
            else
                log(WARNING, '[custom-projectiles] entity records not available; ' .. #pending.looks
                    .. ' saved custom graphics IDs left unchanged')
            end
        end
        if rebuild then rebuild() end
    end
    return state
end
return M
