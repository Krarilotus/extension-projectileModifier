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
    local state = {blocks=blocks, config=canonical(config)}
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
        assert(handle:get('config') == self.config, '[custom-projectiles] saved projectile settings differ; restore the settings used for this save')
        local pending = {}
        for i, block in ipairs(self.blocks) do
            local name = block[1] .. '.bin'
            assert(handle:exists(name), '[custom-projectiles] missing saved state: ' .. name)
            local bytes = handle:get(name)
            assert(type(bytes) == 'string' and #bytes == block[3], '[custom-projectiles] invalid saved state: ' .. name)
            if block[4] then
                assert(bytes==core.readString(block[2],block[3]),
                    '[custom-projectiles] saved graphics-slot layout differs; restore the same extensions and sprite configuration')
            end
            if limits[block[1]] then
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
            local bytes = {}
            for j = 1, #pending[i] do bytes[j] = pending[i]:byte(j) end
            core.writeBytes(block[2], bytes)
        end
        if rebuild then rebuild() end
    end
    return state
end
return M
