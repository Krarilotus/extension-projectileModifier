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
--     layout: flying projectiles and placed decorations take their default
--     look, gameplay state is kept;
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

-- blocks: {name, address, size, layout} with `units=true` on per-unit blocks
-- (size = capacity * 4). Layout blocks are rebuilt from the current
-- configuration and never restored.
function M.new(blocks, config, profile_count, rebuild, capacity)
    local gameplay = {units=config.units, projectiles=config.projectiles, decorations=config.decorations}
    if config.projectile_physics then gameplay.projectile_physics = config.projectile_physics end
    -- Load policy is not gameplay identity. Existing saves keep the same
    -- fingerprint when their gameplay fields have not changed.
    local state = {blocks=blocks, allow_config_changes=config.allow_config_changes_on_load ~= false,
        config=canonical(gameplay), capacity=capacity,
        assets=canonical({projectiles=config.projectiles or {}, decorations=config.decorations or {}})}
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
        local notes, reset_visuals = {}, false
        if changed then
            notes[#notes+1] = 'projectile settings changed since this save; firing timers were reset'
            if handle:exists('assets') then
                reset_visuals = handle:get('assets') ~= self.assets
            end
        end
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
                local same = bytes == core.readString(block[2], block[3])
                assert(same or self.allow_config_changes,
                    '[custom-projectiles] saved graphics-slot layout differs; restore the same extensions and sprite configuration')
                if not same then reset_visuals = true end
            elseif changed and not handle:exists('assets') and retained[block[1]] and block[1] ~= 'seed'
                    and not empty(bytes) then
                -- A format-5 save without an asset identity cannot show that
                -- its graphics IDs still mean the same thing after an edit.
                reset_visuals = true
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
        if reset_visuals then
            notes[#notes+1] = 'custom projectile/decoration graphics changed; flying projectiles and decorations use their default look'
        end
        pending.reset_visuals = reset_visuals
        return pending
    end
    function state:deserialize(handle)
        local pending = self:validate(handle)
        if not pending then self:initialize(); return end
        for _, note in ipairs(pending.notes) do log(WARNING, '[custom-projectiles] ' .. note) end
        if pending.fresh then self:initialize(); return end
        for i, block in ipairs(self.blocks) do
            if block[4] then
                -- rebuilt by rebuild() below
            elseif (pending.reconfigure and not retained[block[1]])
                    or (pending.reset_visuals and retained[block[1]] and block[1] ~= 'seed') then
                core.setMemory(block[2], 0, block[3])
            else
                local bytes = {}
                for j = 1, #pending[i] do bytes[j] = pending[i]:byte(j) end
                core.writeBytes(block[2], bytes)
            end
        end
        if rebuild then rebuild() end
    end
    return state
end
return M
