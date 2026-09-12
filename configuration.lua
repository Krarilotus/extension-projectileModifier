-- Validate the whole configuration before resolving or patching native code.
local constants = require('constants')
local M = {}

-- Inspect effective profiles after validate() has merged sparse overrides.
-- Initialization consumers share this traversal so conditional capabilities
-- include fortification and decoration profiles consistently.
function M.any_profile(cfg, predicate)
    if predicate(cfg) then return true end
    if cfg.on_fortification and predicate(cfg.on_fortification) then return true end
    for _, rule in ipairs(cfg.near_decorations or {}) do
        if predicate(rule.ground) or predicate(rule.fortified) then return true end
    end
    return false
end

M.numbers = {
    count = {1, 64, 1}, cow_count = {1, 64, 1}, spread = {0, 800, 0}, inaccuracy = {0, 800, 0},
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
    preload = true, sync_to_animation = true, turn_before_shot = true,
}
M.units = {}
for id, name in ipairs(constants.unit_names) do
    M.units[name] = id
end
local projectile_ids = {}
for _, id in pairs(constants.projectile_names) do projectile_ids[id] = true end

local function fail(path, reason)
    error('[custom-projectiles] ' .. path .. ': ' .. reason, 0)
end
local function object(value, path)
    if type(value) ~= 'table' then fail(path, 'expected a mapping') end
end

local function validate_flat(config, variants)
    object(config, 'config')
    for key in pairs(config) do
        if key ~= 'units' and key ~= 'projectiles' and key ~= 'decorations' then fail(tostring(key), 'unknown section; expected units, projectiles or decorations') end
    end
    local units = config.units
    if units == nil then units = {} end
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
            elseif key == 'projectile' or key == 'cow_projectile' then
                local variant = variants and variants[value]
                local id = variant and variant.id or (type(value) == 'string' and constants.projectile_names[value] or value)
                if not variant and not projectile_ids[id] then fail(field, 'unknown or unsafe projectile type') end
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
        -- Each state interval enables automatic fire independently. Without a
        -- fallback, unconfigured states hold fire. Keep the native scheduler's
        -- positive enable value internal; chooseInterval selects the state rate.
        if out.interval == nil and (out.interval_moving ~= nil or out.interval_standing ~= nil
            or out.attached_interval ~= nil) then
            out.interval_moving = out.interval_moving or 0
            out.interval_standing = out.interval_standing or 0
            out.interval = math.max(1, out.interval_standing, out.interval_moving, out.attached_interval or 0)
        end
        if not out.interval and out.stagger_max ~= nil then
            fail(path .. '.stagger_max', 'requires an automatic-fire interval: interval, interval_moving, interval_standing or attached_interval')
        end
        if out.interval then
            -- Native reload must not bypass the engine's normal crew gate.
            -- Explicit 0/false still deliberately permits unmanned fire.
            if out.require_manned == nil and out.sync_to_animation ~= false then
                out.require_manned = constants.native_reload_crews[name]
            end
            -- Independent timers may be explicitly combined with native shots.
            if out.suppress_default == nil then out.suppress_default = true end
            if out.projectile == nil then
                out.projectile = constants.native_projectiles[name] or constants.projectile_names.arrow
            end
        end
        if next(out) ~= nil then result.units[name] = out end
    end
    return result
end

function M.validate(config)
    object(config, 'config')
    local variants = require('sprite_resources').definitions(config.projectiles)
    local decorations = require('decorations')
    local definitions = decorations.definitions(config.decorations)
    local units = config.units
    if units == nil then units = {} end
    object(units, 'units')
    local plain, fortified = {}, {}
    for name, settings in pairs(units) do
        object(settings, 'units.' .. tostring(name))
        local base = {}
        for key, value in pairs(settings) do
            if key ~= 'on_fortification' and key ~= 'near_decorations' then base[key] = value end
        end
        plain[name] = base
        if settings.on_fortification ~= nil then
            object(settings.on_fortification, 'units.' .. tostring(name) .. '.on_fortification')
            for _, key in ipairs({'spread', 'inaccuracy'}) do
                if settings.on_fortification[key] ~= nil and settings.on_fortification[key .. '_tiles'] ~= nil then
                    fail('units.' .. name .. '.on_fortification', 'use only one of ' .. key .. ' and ' .. key .. '_tiles')
                end
            end
            local merged = {}
            for key, value in pairs(base) do merged[key] = value end
            for key, value in pairs(settings.on_fortification) do
                if key == 'on_fortification' then fail('units.' .. name, 'nested fortification overrides are not supported') end
                merged[key] = value
                -- An override may use a different unit system than its parent.
                if key == 'spread' or key == 'inaccuracy' then merged[key .. '_tiles'] = nil end
                if key == 'spread_tiles' then merged.spread = nil end
                if key == 'inaccuracy_tiles' then merged.inaccuracy = nil end
            end
            if next(settings.on_fortification) ~= nil then fortified[name] = merged end
        end
    end
    local copied = {}
    for key, value in pairs(config) do copied[key] = value end
    copied.units = plain
    local result = validate_flat(copied, variants)
    local alternates = validate_flat({units=fortified}, variants)
    if next(variants) then result.projectiles = variants end
    if next(definitions) then result.decorations = definitions end
    for name in pairs(fortified) do
        result.units[name] = result.units[name] or {}
        result.units[name].on_fortification = alternates.units[name] or {}
    end
    for name, settings in pairs(units) do
        local rules = decorations.rules(settings.near_decorations, definitions, name)
        if #rules > 0 then
            local function effective(parent, fields)
                local merged = {}
                for key, value in pairs(parent) do merged[key] = value end
                for key, value in pairs(fields) do
                    merged[key] = value
                    if key == 'spread' or key == 'inaccuracy' then merged[key .. '_tiles'] = nil end
                    if key == 'spread_tiles' then merged.spread = nil end
                    if key == 'inaccuracy_tiles' then merged.inaccuracy = nil end
                end
                return validate_flat({units={[name]=merged}}, variants).units[name] or {}
            end
            for _, rule in ipairs(rules) do
                -- Validate sparse fields as part of their effective profile,
                -- so inherited interval/stagger dependencies remain meaningful.
                for _, key in ipairs({'spread', 'inaccuracy'}) do
                    if rule.fields[key] ~= nil and rule.fields[key .. '_tiles'] ~= nil then
                        fail('units.' .. name .. '.near_decorations', 'use only one accuracy/spread unit system')
                    end
                end
                rule.ground = effective(plain[name], rule.fields)
                rule.fortified = effective(fortified[name] or plain[name], rule.fields)
                rule.fields = nil
            end
            result.units[name] = result.units[name] or {}
            result.units[name].near_decorations = rules
        end
    end
    return result
end

return M
