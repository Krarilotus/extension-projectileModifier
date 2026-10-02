-- map-extensions owns save/load and new-world initialization. Only simulation
-- state belongs here; configuration, code and temporary targeting scratch do not.
local M = {}
local function canonical(value)
    if type(value) ~= 'table' then return type(value) .. ':' .. tostring(value) end
    local keys, parts = {}, {}
    for key in pairs(value) do keys[#keys+1] = key end
    table.sort(keys, function(a,b) return tostring(a) < tostring(b) end)
    for _, key in ipairs(keys) do parts[#parts+1] = canonical(key) .. '=' .. canonical(value[key]) end
    return '{' .. table.concat(parts, ';') .. '}'
end
function M.new(blocks, config, profile_count, rebuild)
    local gameplay = {units=config.units, projectiles=config.projectiles, decorations=config.decorations}
    if config.projectile_physics then gameplay.projectile_physics = config.projectile_physics end
    -- Load policy is not gameplay identity. Existing format-5 saves keep the
    -- same fingerprint when their gameplay fields have not changed.
    local state = {blocks=blocks, allow_config_changes=config.allow_config_changes_on_load ~= false,
        config=canonical(gameplay),
        assets=canonical({projectiles=config.projectiles or {}, decorations=config.decorations or {}})}
    local no_assets = not next(config.projectiles or {}) and not next(config.decorations or {})
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
        handle:put('format', '5')
        handle:put('config', self.config)
        handle:put('assets', self.assets)
        for _, block in ipairs(self.blocks) do
            handle:put(block[1] .. '.bin', core.readString(block[2], block[3]))
        end
    end
    -- Map Extensions calls this before restoring any extension. Direct restores
    -- use the same validator; no pending state is retained between callbacks.
    function state:validate(handle)
        local present = handle:exists('format')
        if not present and not handle.required then return end
        assert(present and handle:get('format') == '5', '[custom-projectiles] unsupported saved state format; start a new match with this version')
        local saved_config = handle:get('config')
        assert(type(saved_config) == 'string' and saved_config:sub(1,1) == '{' and saved_config:sub(-1) == '}',
            '[custom-projectiles] invalid saved projectile configuration')
        local changed = saved_config ~= self.config
        assert(not changed or self.allow_config_changes,
            '[custom-projectiles] saved projectile settings differ; restore the settings used for this save or enable allow_config_changes_on_load')
        if changed then
            if handle:exists('assets') then
                assert(handle:get('assets') == self.assets,
                    '[custom-projectiles] custom projectile/decorations changed; restore their definitions for this save')
            else
                -- Legacy saves have no asset fingerprint. Only an empty
                -- visual state proves their IDs cannot be reinterpreted.
                assert(no_assets, '[custom-projectiles] legacy save has no asset identity; load once with its original config and resave before editing')
            end
        end
        local pending = {reconfigure=changed}
        for i, block in ipairs(self.blocks) do
            local name = block[1] .. '.bin'
            assert(handle:exists(name), '[custom-projectiles] missing saved state: ' .. name)
            local bytes = handle:get(name)
            assert(type(bytes) == 'string' and #bytes == block[3], '[custom-projectiles] invalid saved state: ' .. name)
            if block[4] then
                assert(bytes==core.readString(block[2],block[3]),
                    '[custom-projectiles] saved graphics-slot layout differs; restore the same extensions and sprite configuration')
            end
            if changed and not handle:exists('assets') and (retained[block[1]] and block[1] ~= 'seed' or block[4]) then
                assert(bytes == string.rep('\0', #bytes),
                    '[custom-projectiles] legacy save contains custom graphics; load with its original config and resave before editing')
            end
            if limits[block[1]] and not (changed and block[1] == 'profile') then
                for offset = 1, #bytes, 4 do
                    local a,b,c,d = bytes:byte(offset, offset+3)
                    local value = a + b*256 + c*65536 + d*16777216
                    assert(value <= limits[block[1]], '[custom-projectiles] out-of-range saved state: ' .. name)
                end
            end
            pending[i] = bytes
        end
        return pending
    end
    function state:deserialize(handle)
        local pending = self:validate(handle)
        if not pending then self:initialize(); return end
        for i, block in ipairs(self.blocks) do
            if pending.reconfigure and not retained[block[1]] and not block[4] then
                core.setMemory(block[2], 0, block[3])
            elseif not block[4] then
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
