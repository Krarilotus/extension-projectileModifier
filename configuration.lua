-- Validate the whole configuration before resolving or patching native code.
local constants = require('constants')
local M = {}
M.numbers = {
    count = {1, 64, 1}, spread = {0, 800, 0}, inaccuracy = {0, 800, 0},
    spread_tiles = {0, 100, 0}, inaccuracy_tiles = {0, 100, 0},
    interval = {1, 60000, 100}, interval_moving = {0, 60000, 100},
    interval_standing = {0, 60000, 100}, range = {1, 100, 20},
    wall_min_distance = {0, 100, 3}, require_manned = {0, 4, 0},
    shoot_height = {0, 500, 0}, stagger_min = {1, 60000, 1},
    stagger_max = {0, 60000, 0}, density_min = {1, 256, 1},
    density_radius = {1, 100, 5}, attached_interval = {0, 60000, 100},
    attached_board_radius = {0, 100, 2}, preload_poll = {1, 60000, 5},
    sync_max_wait = {1, 60000, 40},
}
M.booleans = {
    suppress_default = true, random_targets = true, attached_ignore_crew = true,
    attached_stop_when_boarded = true, ai_cow_vs_units = true, ai_only = true,
    preload = true, sync_to_animation = true,
}
M.units, M.ids = {}, {}
for id, name in ipairs(constants.unit_names) do
    M.units[name] = id
    M.ids[name:lower():gsub('[^a-z0-9]+', '_')] = name
end
local projectile_ids = {}
for _, id in pairs(constants.projectile_names) do projectile_ids[id] = true end

local function fail(path, reason)
    error('[projectileModifier] ' .. path .. ': ' .. reason, 0)
end
local function object(value, path)
    if type(value) ~= 'table' then fail(path, 'expected a mapping') end
end

function M.validate(config)
    object(config, 'config')
    for key in pairs(config) do
        if key ~= 'units' then fail(tostring(key), 'unknown section; expected units') end
    end
    local units = config.units or {}
    object(units, 'units')
    local result = {units = {}}
    for name, cfg in pairs(units) do
        local path = 'units.' .. tostring(name)
        if not M.units[name] then fail(path, 'unknown unit name') end
        object(cfg, path)
        local out = {}
        for key, value in pairs(cfg) do
            local field = path .. '.' .. tostring(key)
            local bounds = M.numbers[key]
            if bounds then
                if key == 'require_manned' and type(value) == 'boolean' then value = value and 1 or 0 end
                if type(value) ~= 'number' or value ~= value or value % 1 ~= 0
                    or value < bounds[1] or value > bounds[2] then
                    fail(field, 'expected an integer from ' .. bounds[1] .. ' to ' .. bounds[2])
                end
                out[key] = value
            elseif M.booleans[key] then
                if type(value) ~= 'boolean' then fail(field, 'expected true or false') end
                out[key] = value
            elseif key == 'projectile' then
                local id = type(value) == 'string' and constants.projectile_names[value] or value
                if not projectile_ids[id] then fail(field, 'unknown or unsafe projectile type') end
                out[key] = id
            elseif key == 'targets' then
                if type(value) == 'string' then value = {value} end
                object(value, field)
                local count, seen, targets = 0, {}, {}
                for index in pairs(value) do
                    if type(index) ~= 'number' or index % 1 ~= 0 or index < 1 or index > #value then
                        fail(field, 'expected a list of target kinds')
                    end
                    count = count + 1
                end
                if count < 1 or count > 4 or count ~= #value then fail(field, 'use one to four target kinds') end
                for _, kind in ipairs(value) do
                    if not constants.target_kinds[kind] or seen[kind] then fail(field, 'unknown or duplicate target kind') end
                    seen[kind] = true
                    targets[#targets+1] = kind
                end
                out[key] = targets
            else
                fail(field, 'unknown setting')
            end
        end
        for _, key in ipairs({'spread', 'inaccuracy'}) do
            if out[key] ~= nil and out[key .. '_tiles'] ~= nil then fail(path, 'use only one of ' .. key .. ' and ' .. key .. '_tiles') end
        end
        if (out.stagger_max or 0) > 0 and (out.stagger_min or 1) > out.stagger_max then
            fail(path, 'stagger_min must not exceed stagger_max')
        end
        if out.stagger_min and not out.stagger_max then fail(path, 'stagger_min requires stagger_max') end
        if not out.interval then
            for _, key in ipairs({'interval_moving', 'interval_standing', 'attached_interval', 'stagger_max'}) do
                if out[key] ~= nil then fail(path .. '.' .. key, 'requires interval') end
            end
        end
        if out.interval then
            -- A timer replaces the native schedule unless explicitly combined.
            if out.suppress_default == nil then out.suppress_default = true end
            if out.projectile == nil then
                out.projectile = constants.native_projectiles[name] or constants.projectile_names.arrow
            end
        end
        if next(out) ~= nil then result.units[name] = out end
    end
    return result
end

-- GUI controls are optional overrides. Disabled controls preserve file values.
function M.merge(file, gui)
    local result = {units = {}}
    file = file or {units = {}}
    object(file, 'file')
    -- Check unknown sections without normalizing (normalization adds defaults).
    for key in pairs(file) do if key ~= 'units' then fail(tostring(key), 'unknown section') end end
    object(file.units or {}, 'file.units')
    for name, cfg in pairs(file.units or {}) do
        object(cfg, 'units.' .. tostring(name))
        result.units[name] = {}
        for key, value in pairs(cfg) do result.units[name][key] = value end
    end
    object(gui or {}, 'customizations')
    for slug, settings in pairs(gui or {}) do
        local name = M.ids[slug]
        if not name then fail(tostring(slug), 'unknown GUI unit') end
        object(settings, slug)
        for key, control in pairs(settings) do
            if not M.numbers[key] and not M.booleans[key] and key ~= 'projectile' and key ~= 'targets' then
                fail(slug .. '.' .. tostring(key), 'unknown GUI setting')
            end
            local value
            if key == 'projectile' or key == 'targets' or M.booleans[key] then
                if control ~= 'inherit' then
                    value = control
                    if M.booleans[key] then
                        if control ~= 'yes' and control ~= 'no' then fail(slug .. '.' .. key, 'invalid choice') end
                        value = control == 'yes'
                    elseif key == 'targets' then
                        local presets = {
                            units = {'units'}, buildings = {'buildings'}, fortifications = {'fortifications'},
                            siege_towers = {'siege_towers'}, cluster = {'cluster'}, walls = {'walls'},
                            units_buildings = {'units', 'fortifications', 'buildings'},
                        }
                        value = presets[control]
                        if not value then fail(slug .. '.targets', 'invalid target preset') end
                    end
                end
            else
                object(control, slug .. '.' .. key)
                if type(control.enabled) ~= 'boolean' then fail(slug .. '.' .. key, 'missing enabled flag') end
                if control.enabled then value = control.sliderValue; if value == nil then fail(slug .. '.' .. key, 'missing value') end end
            end
            if value ~= nil then
                result.units[name] = result.units[name] or {}
                local cfg = result.units[name]
                if key == 'spread_tiles' then cfg.spread = nil end
                if key == 'inaccuracy_tiles' then cfg.inaccuracy = nil end
                cfg[key] = value
            end
        end
    end
    return M.validate(result)
end

return M
