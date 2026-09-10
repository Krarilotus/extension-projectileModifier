local addresses = require("addresses")
local constants = require("constants")
local templates = require("templates")
local configuration = require('configuration')

local namespace = {}

local unit_names       = constants.unit_names
local projectile_names = constants.projectile_names
local MAX_TYPES        = constants.MAX_UNIT_TYPES
local MAX_UNITS        = addresses.max_units

local function resolve()
local function locate(pattern)
    local ok, address = pcall(core.scanForAOB, pattern, 0x400000, 0x700000)
    assert(ok and type(address) == 'number' and address >= 0x400000 and address < 0x700000,
        '[projectileModifier] unsupported executable or conflicting module at signature: ' .. pattern)
    local found, duplicate = pcall(core.scanForAOB, pattern, address + 1, 0x700000)
    assert(not found or type(duplicate) ~= 'number' or duplicate <= 0,
        '[projectileModifier] ambiguous native signature: ' .. pattern)
    return address
end

-- UnitsState::fireUnitProjectile(unitID, entityType, targetX, targetY, targetZ)
-- thiscall, ecx = unit array base - 0x614. Every shooting unit in the game
-- funnels through here before EntityState::spawnProjectileEntity is reached.
local fire_projectile_addr = locate("53 56 57 8B 7C 24 14 33 C0 33 D2 83 FF 03 0F 85")

-- UnitsState::acquireShootTarget(unitID) -> bool, thiscall, ret 4.
-- Fills unit+0xBE/0xC0/0xC2 with the target position.
local acquire_target_addr = locate("83 EC 40 53 56 57 8B 7C 24 50 69 FF 90 04 00 00 8B F1 0F BF 84 37 AA 06 00 00")

-- Inside UnitsState::updateUnits, reached once per tick for every living unit.
local unit_tick_addr = locate("83 C2 01 89 16 8B 15 ? ? ? ? 69 D2 90 04 00 00 33 C9 66 89 8C 32 AE 09 00 00")

-- Tile layer bases, read out of the wall-validation code inside acquireShootTarget.
local tile_rows_addr  = core.readInteger(locate("8D 14 40 8B 1C 95 ? ? ? ?") + 6)
local tile_flags_addr = core.readInteger(locate("F7 04 9D ? ? ? ? 00 01 00 00") + 3)
-- Ground height per tile, read from the wall-height maths in acquireShootTarget.
local terrain_height_addr = core.readInteger(locate("8A 8B ? ? ? ? 0F B6 83 ? ? ? ? 0F B6 D1") + 9)
-- Team table, indexed by player id. The game consults this exact table before
-- letting a unit shoot at another, so using it keeps us from targeting allies.
local team_table_addr = core.readInteger(locate("8B 0C 85 ? ? ? ? 8B 44 24 30 3B 0C 85 ? ? ? ?") + 3)

-- Building array base, read from any `imul ecx,0x32C; mov edx,[ecx+base+0xD8]`.
local building_base_addr = core.readInteger(locate("69 C9 2C 03 00 00 8B 91 ? ? ? ? 3B 94 37 B4 09 00 00") + 8) - 0xD8

-- AI character files: the array base, and the per-player index into it.
local aic_array_base = core.readInteger(locate(
    "? ? ? ? E8 ? ? ? ? 89 1D ? ? ? ? 83 3D ? ? ? ? 00 75 44 6A 08 B9 ? ? ? ? E8 ? ? ? ? 85 C0 74 34 8B C5 2B 05"))
local player_aic_addr = core.readInteger(locate(
    "69 C0 F4 39 00 00 8B 88 ? ? ? ? 69 C9 A4 02 00 00") + 8)
-- The stored index is 1-based, so bias the base by one character block and
-- fold in the field offset, letting the assembly do a single indexed read.
local AIC_STRIDE = constants.AIC_FIELD_COUNT * 4
local aic_cow_addr = aic_array_base - AIC_STRIDE
                     + constants.AIC_COW_THROW_INTERVAL * 4

local unit_array_base = addresses.unit_array_base_addr
assert(core.readInteger(fire_projectile_addr + 0x23) - 0x3B0 == unit_array_base,
    '[projectileModifier] unit array does not match this executable')
local unit_state_this = unit_array_base - 0x614
local current_unit_id_addr = core.readInteger(unit_tick_addr + 7)
assert(core.readInteger(unit_tick_addr + 0x3A4) == MAX_UNITS,
    '[projectileModifier] unsupported unit-array capacity modification')
return {fire=fire_projectile_addr, acquire=acquire_target_addr, tick=unit_tick_addr,
    rows=tile_rows_addr, flags=tile_flags_addr, terrain=terrain_height_addr,
    teams=team_table_addr, buildings=building_base_addr, aic=aic_array_base,
    playerAic=player_aic_addr, cow=aic_cow_addr, units=unit_array_base,
    this=unit_state_this, current=current_unit_id_addr}
end

-- Private tables, non-overlapping scratch and persistent per-unit firing state.
local TABLE_BYTES = MAX_TYPES * 4
local OFF_REENTRY   = 0x00
local OFF_SEED      = 0x04
local OFF_SCATY     = 0x08
local OFF_REMAP     = 0x10
local OFF_COUNT     = OFF_REMAP    + TABLE_BYTES
local OFF_SPREAD    = OFF_COUNT    + TABLE_BYTES
local OFF_INTERVAL  = OFF_SPREAD   + TABLE_BYTES
local OFF_SUPPRESS  = OFF_INTERVAL + TABLE_BYTES
local OFF_FORCED    = OFF_SUPPRESS + TABLE_BYTES
local OFF_COOLDOWN  = OFF_FORCED   + TABLE_BYTES
local OFF_ORDER     = OFF_COOLDOWN + MAX_UNITS * 4   -- 4 target kinds per unit type
local OFF_RANGE     = OFF_ORDER    + MAX_TYPES * 4
local OFF_WALLMIN   = OFF_RANGE    + TABLE_BYTES
local OFF_MULTI     = OFF_WALLMIN  + TABLE_BYTES     -- random-target volleys
local OFF_HEIGHT    = OFF_MULTI    + TABLE_BYTES     -- extra firing height
local OFF_MANNED    = OFF_HEIGHT   + TABLE_BYTES     -- crew members required
local OFF_BLDCLASS  = OFF_MANNED   + TABLE_BYTES     -- byte per building type
local OFF_SCRATCH   = OFF_BLDCLASS + constants.MAX_BUILDING_TYPES
local OFF_CANDS     = OFF_SCRATCH  + 0x100           -- scratch includes fields through 0xB0
local OFF_IMOVE     = OFF_CANDS    + constants.MAX_CANDIDATES * 4
local OFF_ISTAND    = OFF_IMOVE    + TABLE_BYTES
local OFF_LASTPOS   = OFF_ISTAND   + TABLE_BYTES     -- packed position, per unit
local OFF_MOVECD    = OFF_LASTPOS  + MAX_UNITS * 4   -- ticks left counting as moving
local OFF_STAGMIN   = OFF_MOVECD   + MAX_UNITS * 4
local OFF_STAGMAX   = OFF_STAGMIN  + TABLE_BYTES
local OFF_PENDING   = OFF_STAGMAX  + TABLE_BYTES     -- projectiles still owed
local OFF_PENDCD    = OFF_PENDING  + MAX_UNITS * 4   -- ticks until the next one
local OFF_DMIN      = OFF_PENDCD   + MAX_UNITS * 4   -- enemies needed in a cluster
local OFF_DRAD      = OFF_DMIN     + TABLE_BYTES     -- cluster radius, tiles
local OFF_ATTINT    = OFF_DRAD     + TABLE_BYTES     -- interval while attached
local OFF_ATTCREW   = OFF_ATTINT   + TABLE_BYTES     -- attached ignores the crew
local OFF_ATTBOARD  = OFF_ATTCREW  + TABLE_BYTES     -- stop when enemies board
local OFF_ATTBR2    = OFF_ATTBOARD + TABLE_BYTES     -- boarding radius, squared
local OFF_AICOW     = OFF_ATTBR2   + TABLE_BYTES     -- AI lords may send cows
local OFF_PRELOAD   = OFF_AICOW    + TABLE_BYTES     -- hold a loaded weapon ready
local OFF_PRELPOLL  = OFF_PRELOAD  + TABLE_BYTES
local OFF_SYNC      = OFF_PRELPOLL + TABLE_BYTES     -- fire on an animation beat
local OFF_SYNCMAX   = OFF_SYNC     + TABLE_BYTES
local OFF_SYNCWAIT  = OFF_SYNCMAX  + TABLE_BYTES     -- per unit, ticks waited
local OFF_INACC     = OFF_SYNCWAIT + MAX_UNITS * 4   -- per-shot aiming error
local OFF_AIONLY    = OFF_INACC    + TABLE_BYTES     -- leave the player's units alone
local OFF_UID       = OFF_AIONLY   + TABLE_BYTES
local OFF_IDENTITY  = OFF_UID      + MAX_UNITS * 4
local OFF_NATIVESEEN = OFF_IDENTITY + MAX_UNITS * 4
local DATA_SIZE     = OFF_NATIVESEEN + MAX_UNITS * 4

local data_addr = nil
local volley_addr = nil
local apply_unit
local installed = false
local persistent

local function unit_type_id(name)
    local index = table.find(unit_names, name)
    if index == nil then
        log(WARNING, "[projectileModifier] unknown unit name: " .. tostring(name))
    end
    return index
end

local function projectile_id(value)
    if type(value) == "number" then
        return math.floor(value)
    end
    local id = projectile_names[value]
    if id == nil then
        log(WARNING, "[projectileModifier] unknown projectile name: " .. tostring(value))
    end
    return id
end

local function set_entry(table_offset, type_id, value)
    core.writeInteger(data_addr + table_offset + 4 * type_id, value)
end

-- Writes the four target-kind slots for one unit type. Order is priority order:
-- the first kind that finds something wins, the rest are not consulted.
local function set_targets(type_id, list)
    if type(list) == "string" then list = { list } end
    local slot = 0
    for _, name in ipairs(list) do
        local kind = constants.target_kinds[name]
        if kind == nil then
            log(WARNING, "[projectileModifier] unknown target kind: " .. tostring(name))
        elseif slot >= 4 then
            log(WARNING, "[projectileModifier] more than four target kinds listed, ignoring " .. tostring(name))
        else
            core.writeByte(data_addr + OFF_ORDER + 4 * type_id + slot, kind)
            slot = slot + 1
        end
    end
    for i = slot, 3 do
        core.writeByte(data_addr + OFF_ORDER + 4 * type_id + i, 0)
    end
end

-- FASM is handed a fixed memory budget by the framework, and every constant in
-- `values` is prepended to every script it assembles. Keeping each script small
-- -- comments stripped, only the constants it actually mentions -- is what keeps
-- the assembler inside that budget.
local NEWLINE = string.char(10)

local function assemble_blob(script, values)
    local lines = {}
    for raw in (script .. NEWLINE):gmatch("([^" .. NEWLINE .. "]*)" .. NEWLINE) do
        local line = raw:gsub(";.*$", ""):gsub("^%s+", ""):gsub("%s+$", "")
        if line ~= "" then
            lines[#lines + 1] = line
        end
    end
    local body = table.concat(lines, NEWLINE)

    local used = {}
    for name, value in pairs(values) do
        if body:find("%f[%w_]" .. name .. "%f[^%w_]") then
            used[name] = value
        end
    end
    return core.allocateAssembly(body, used)
end

local function install(config)
    local native = resolve()
    local fire_projectile_addr, acquire_target_addr, unit_tick_addr = native.fire, native.acquire, native.tick
    local tile_rows_addr, tile_flags_addr, terrain_height_addr = native.rows, native.flags, native.terrain
    local team_table_addr, building_base_addr = native.teams, native.buildings
    local aic_array_base, player_aic_addr, aic_cow_addr = native.aic, native.playerAic, native.cow
    local unit_array_base, unit_state_this, current_unit_id_addr = native.units, native.this, native.current
    data_addr = core.allocate(DATA_SIZE, true)
    core.writeInteger(data_addr + OFF_SEED, 0x1D872B41)

    -- -1 in the remap table means "leave the game's choice alone".
    for i = 0, MAX_TYPES - 1 do
        core.writeInteger(data_addr + OFF_REMAP + 4 * i, 0xFFFFFFFF)
        core.writeInteger(data_addr + OFF_RANGE + 4 * i, constants.DEFAULT_RANGE)
        core.writeInteger(data_addr + OFF_WALLMIN + 4 * i, constants.DEFAULT_WALL_MIN_DISTANCE)
        core.writeInteger(data_addr + OFF_DRAD + 4 * i, constants.DEFAULT_DENSITY_RADIUS)
        core.writeInteger(data_addr + OFF_PRELPOLL + 4 * i, constants.DEFAULT_PRELOAD_POLL)
        core.writeInteger(data_addr + OFF_SYNCMAX + 4 * i, constants.DEFAULT_SYNC_MAX_WAIT)
        -- -1: an attached unit keeps its usual rate unless told otherwise.
        core.writeInteger(data_addr + OFF_ATTINT + 4 * i, 0xFFFFFFFF)
        core.writeInteger(data_addr + OFF_ATTCREW + 4 * i, 1)
        core.writeInteger(data_addr + OFF_ATTBOARD + 4 * i, 1)
        core.writeInteger(data_addr + OFF_ATTBR2 + 4 * i,
            constants.DEFAULT_BOARD_RADIUS * constants.DEFAULT_BOARD_RADIUS)
        -- default target list: enemy units only, matching the game's own behaviour
        core.writeByte(data_addr + OFF_ORDER + 4 * i, constants.target_kinds.units)
    end

    -- Every building type is a plain building unless it is a fortification.
    for t = 1, constants.MAX_BUILDING_TYPES - 1 do
        core.writeByte(data_addr + OFF_BLDCLASS + t, constants.target_kinds.buildings)
    end
    for _, t in ipairs(constants.fortification_types) do
        core.writeByte(data_addr + OFF_BLDCLASS + t, constants.target_kinds.fortifications)
    end
    -- Attached siege towers get their own class so they can be singled out
    -- rather than being lost among farms and housing under `buildings`.
    for _, t in ipairs(constants.siege_tower_types) do
        core.writeByte(data_addr + OFF_BLDCLASS + t, constants.target_kinds.siege_towers)
    end

    local values = {
        REENTRY       = data_addr + OFF_REENTRY,
        SEED          = data_addr + OFF_SEED,
        SCATY         = data_addr + OFF_SCATY,
        REMAPT        = data_addr + OFF_REMAP,
        COUNTT        = data_addr + OFF_COUNT,
        SPREADT       = data_addr + OFF_SPREAD,
        INTERVALT     = data_addr + OFF_INTERVAL,
        SUPPRESST     = data_addr + OFF_SUPPRESS,
        FORCEDT       = data_addr + OFF_FORCED,
        COOLDOWNT     = data_addr + OFF_COOLDOWN,
        UNITSTATE     = unit_state_this,
        UNITARRAY     = unit_array_base,
        UNITTYPEBASE  = unit_array_base + constants.OFFSET_UNIT_TYPE,
        CURUNIT       = current_unit_id_addr,
        FIREPROJ      = fire_projectile_addr,
        ACQUIRE       = acquire_target_addr,
        MAXTYPES      = MAX_TYPES,
        MAXUNITS      = MAX_UNITS,
        ORDERT        = data_addr + OFF_ORDER,
        RANGET        = data_addr + OFF_RANGE,
        WALLMINT      = data_addr + OFF_WALLMIN,
        MULTIT        = data_addr + OFF_MULTI,
        HEIGHTT       = data_addr + OFF_HEIGHT,
        MANNEDT       = data_addr + OFF_MANNED,
        BLDCLASST     = data_addr + OFF_BLDCLASS,
        BLDBASE       = building_base_addr,
        MAXBLD        = constants.MAX_BUILDINGS,
        TILEROWS      = tile_rows_addr,
        TILEFLAGS     = tile_flags_addr,
        S_UNITPTR     = data_addr + OFF_SCRATCH + 0x00,
        S_TX          = data_addr + OFF_SCRATCH + 0x04,
        S_TY          = data_addr + OFF_SCRATCH + 0x08,
        S_R           = data_addr + OFF_SCRATCH + 0x0C,
        S_R2          = data_addr + OFF_SCRATCH + 0x10,
        S_OWNER       = data_addr + OFF_SCRATCH + 0x14,
        S_CLASS       = data_addr + OFF_SCRATCH + 0x18,
        S_BEST        = data_addr + OFF_SCRATCH + 0x1C,
        S_BESTD       = data_addr + OFF_SCRATCH + 0x20,
        S_WMIN2       = data_addr + OFF_SCRATCH + 0x24,
        S_WX          = data_addr + OFF_SCRATCH + 0x28,
        S_WY          = data_addr + OFF_SCRATCH + 0x2C,
        S_SAVE0       = data_addr + OFF_SCRATCH + 0x30,
        S_SAVE1       = data_addr + OFF_SCRATCH + 0x34,
        S_SAVE2       = data_addr + OFF_SCRATCH + 0x38,
        S_SAVE3       = data_addr + OFF_SCRATCH + 0x3C,
        S_SAVE4       = data_addr + OFF_SCRATCH + 0x40,
        S_SAVE5       = data_addr + OFF_SCRATCH + 0x44,
        S_SAVE6       = data_addr + OFF_SCRATCH + 0x48,
        S_SAVE7       = data_addr + OFF_SCRATCH + 0x4C,
        S_SAVEXY      = data_addr + OFF_SCRATCH + 0xA8,
        S_SAVEZ       = data_addr + OFF_SCRATCH + 0xAC,
        S_SAVETILE    = data_addr + OFF_SCRATCH + 0xB0,
        S_EXPLICIT    = data_addr + OFF_SCRATCH + 0xB4,
        S_SAVECOW     = data_addr + OFF_SCRATCH + 0xB8,
        S_SELF        = data_addr + OFF_SCRATCH + 0x50,
        S_ID          = data_addr + OFF_SCRATCH + 0x54,
        S_INTV        = data_addr + OFF_SCRATCH + 0x58,
        S_MULTI       = data_addr + OFF_SCRATCH + 0x5C,
        S_HEIGHT      = data_addr + OFF_SCRATCH + 0x60,
        S_NCAND       = data_addr + OFF_SCRATCH + 0x64,
        S_SHOOTER     = data_addr + OFF_SCRATCH + 0x68,
        S_SAVEBH      = data_addr + OFF_SCRATCH + 0x6C,
        S_SHOTX       = data_addr + OFF_SCRATCH + 0x70,
        S_SHOTY       = data_addr + OFF_SCRATCH + 0x74,
        S_SHOTZ       = data_addr + OFF_SCRATCH + 0x78,
        S_CANDS       = data_addr + OFF_CANDS,
        MAXCAND       = constants.MAX_CANDIDATES,
        IMOVET        = data_addr + OFF_IMOVE,
        ISTANDT       = data_addr + OFF_ISTAND,
        LASTPOST      = data_addr + OFF_LASTPOS,
        MOVECDT       = data_addr + OFF_MOVECD,
        MOVEHYST      = constants.MOVE_HYSTERESIS,
        STAGMINT      = data_addr + OFF_STAGMIN,
        STAGMAXT      = data_addr + OFF_STAGMAX,
        PENDINGT      = data_addr + OFF_PENDING,
        PENDCDT       = data_addr + OFF_PENDCD,
        DMINT         = data_addr + OFF_DMIN,
        DRADT         = data_addr + OFF_DRAD,
        ATTINTT       = data_addr + OFF_ATTINT,
        ATTCREWT      = data_addr + OFF_ATTCREW,
        ATTBOARDT     = data_addr + OFF_ATTBOARD,
        ATTBR2T       = data_addr + OFF_ATTBR2,
        AICOWT        = data_addr + OFF_AICOW,
        PRELOADT      = data_addr + OFF_PRELOAD,
        PRELPOLLT     = data_addr + OFF_PRELPOLL,
        SYNCT         = data_addr + OFF_SYNC,
        SYNCMAXT      = data_addr + OFF_SYNCMAX,
        SYNCWAITT     = data_addr + OFF_SYNCWAIT,
        INACCT        = data_addr + OFF_INACC,
        AIONLYT       = data_addr + OFF_AIONLY,
        TERRAINH      = terrain_height_addr,
        MAPMICROMAX   = constants.MAP_MICRO_MAX,
        S_INACC       = data_addr + OFF_SCRATCH + 0x5C + 0x44,
        S_MOVED       = data_addr + OFF_SCRATCH + 0x5C + 0x48,
        PLAYERAIC     = player_aic_addr,
        AICCOW        = aic_cow_addr,
        S_MODE        = data_addr + OFF_SCRATCH + 0x5C + 0x38,
        S_PROJ        = data_addr + OFF_SCRATCH + 0x5C + 0x3C,
        S_TEAM        = data_addr + OFF_SCRATCH + 0x5C + 0x40,
        S_ATTACHED    = data_addr + OFF_SCRATCH + 0x5C + 0x30,
        S_BR2         = data_addr + OFF_SCRATCH + 0x5C + 0x34,
        S_DR2         = data_addr + OFF_SCRATCH + 0x5C + 0x28,
        S_DMIN        = data_addr + OFF_SCRATCH + 0x5C + 0x2C,
        S_ONESHOT     = data_addr + OFF_SCRATCH + 0x5C + 0x20,
        S_TMP         = data_addr + OFF_SCRATCH + 0x5C + 0x24,
        TEAMTBL       = team_table_addr,
        RETRYTICKS    = constants.RETRY_TICKS,
        UIDT          = data_addr + OFF_UID,
        IDENTITYT     = data_addr + OFF_IDENTITY,
        NATIVESEENT   = data_addr + OFF_NATIVESEEN,
    }

    for _, name in ipairs(unit_names) do
        if config.units[name] then apply_unit(name, config.units[name]) end
    end

    -- Each blob starts with the routine the others call, so its address is its
    -- entry point. Order matters: a blob may only reference blobs built before it.
    values.FIXSCATTER = assemble_blob(templates.fixscatter_code, values)
    values.RND = assemble_blob(templates.rand_code, values)
    values.SETSTAGGER = assemble_blob(templates.stagger_code, values)
    values.SCANUNIT = assemble_blob(templates.scan_unit_code, values)
    values.SCANCLUSTER = assemble_blob(templates.scan_cluster_code, values)
    values.CHECKATTACHED = assemble_blob(templates.attach_code, values)
    values.ISBOARDED = assemble_blob(templates.board_code, values)
    values.ISAIOWNED = assemble_blob(templates.aiowned_code, values)
    values.WANTSCOW = assemble_blob(templates.aicow_code, values)
    values.SYNCREADY = assemble_blob(templates.sync_code, values)
    values.CHOOSEINTERVAL = assemble_blob(templates.interval_code, values)
    values.RESETUNIT = assemble_blob(templates.identity_code, values)
    values.CREWOK = assemble_blob(templates.crew_code, values)
    values.SCANBLD = assemble_blob(templates.scan_bld_code, values)
    values.SCANWALL = assemble_blob(templates.scan_wall_code, values)
    volley_addr = assemble_blob(templates.volley_code, values)
    values.VOLLEY = volley_addr
    values.PICKTARGET = assemble_blob(templates.pick_code, values)
    values.RESTORETARGET = assemble_blob(templates.restore_code, values)

    -- Fire hook: 5 byte jump plus 2 nops over the 7 byte prologue we replay.
    values.RESUME = fire_projectile_addr + 7
    local fire_hook = assemble_blob(templates.fire_hook_code, values)

    -- Tick hook: exactly 5 bytes (`add edx,1` + `mov [esi],edx`), replayed at the end.
    values.RESUME = unit_tick_addr + 5
    local tick_hook = assemble_blob(templates.tick_hook_code, values)

    -- Prepare persistence and all code before either entry point is redirected.
    persistent = require('state').new({
        {'seed', data_addr + OFF_SEED, 4},
        {'cooldown', data_addr + OFF_COOLDOWN, MAX_UNITS * 4},
        {'lastpos', data_addr + OFF_LASTPOS, MAX_UNITS * 4},
        {'movement', data_addr + OFF_MOVECD, MAX_UNITS * 4},
        {'pending', data_addr + OFF_PENDING, MAX_UNITS * 4},
        {'pending-cooldown', data_addr + OFF_PENDCD, MAX_UNITS * 4},
        {'sync-wait', data_addr + OFF_SYNCWAIT, MAX_UNITS * 4},
        {'uid', data_addr + OFF_UID, MAX_UNITS * 4},
        {'identity', data_addr + OFF_IDENTITY, MAX_UNITS * 4},
    }, config)
    assert(modules['map-extensions'], '[projectileModifier] map-extensions is required')
    modules['map-extensions']:registerSection('projectileModifier', persistent)
    core.writeCode(fire_projectile_addr, {
        0xE9, core.itob(core.getRelativeAddress(fire_projectile_addr, fire_hook, -5)), 0x90, 0x90
    })
    core.writeCode(unit_tick_addr, {
        0xE9, core.itob(core.getRelativeAddress(unit_tick_addr, tick_hook, -5))
    })

    log(INFO, string.format(
        "[projectileModifier] fire=%X acquire=%X tick=%X teams=%X buildings=%X aic=%X data=%X volley=%X",
        fire_projectile_addr, acquire_target_addr, unit_tick_addr, team_table_addr,
        building_base_addr, aic_array_base, data_addr, volley_addr))
end

-- Every key this module understands. Anything else in a unit entry is a typo,
-- and silently ignoring it makes for a long evening.
local KNOWN_KEYS = {
    projectile = true, count = true, spread = true,
    interval = true, interval_moving = true, interval_standing = true,
    suppress_default = true, targets = true, range = true,
    wall_min_distance = true, require_manned = true,
    random_targets = true, shoot_height = true,
    stagger_min = true, stagger_max = true,
    density_min = true, density_radius = true,
    attached_interval = true, attached_ignore_crew = true,
    attached_stop_when_boarded = true, attached_board_radius = true,
    ai_cow_vs_units = true,
    inaccuracy = true, inaccuracy_tiles = true, spread_tiles = true,
    ai_only = true,
    preload = true, preload_poll = true,
    sync_to_animation = true, sync_max_wait = true,
}

apply_unit = function(name, cfg)
    local id = unit_type_id(name)
    if id == nil then return end

    for key, _ in pairs(cfg) do
        if not KNOWN_KEYS[key] then
            log(WARNING, string.format(
                "[projectileModifier] '%s': unknown setting '%s' (check for a comma where a colon belongs)",
                name, tostring(key)))
        end
    end

    if cfg["projectile"] ~= nil then
        local pid = projectile_id(cfg["projectile"])
        if pid ~= nil then
            set_entry(OFF_REMAP, id, pid)
            set_entry(OFF_FORCED, id, pid)
        end
    end

    if cfg["count"] ~= nil then
        set_entry(OFF_COUNT, id, math.max(1, math.floor(cfg["count"])))
    end

    if cfg["spread"] ~= nil then
        set_entry(OFF_SPREAD, id, math.max(0, math.floor(cfg["spread"])))
    end

    -- Same two values in tiles, since that is how everything else is measured.
    if cfg["spread_tiles"] ~= nil then
        set_entry(OFF_SPREAD, id, math.max(0, math.floor(cfg["spread_tiles"] * 8)))
    end

    if cfg["interval"] ~= nil then
        local interval = math.max(1, math.floor(cfg["interval"]))
        set_entry(OFF_INTERVAL, id, interval)
        -- Both states inherit it until told otherwise.
        set_entry(OFF_IMOVE, id, interval)
        set_entry(OFF_ISTAND, id, interval)
        -- A forced shooter needs something to throw; default to an arrow.
        if cfg["projectile"] == nil then
            set_entry(OFF_FORCED, id, projectile_names.arrow)
        end
    end

    -- These override `interval` for one state only. 0 means "hold fire".
    if cfg["interval_moving"] ~= nil then
        set_entry(OFF_IMOVE, id, math.max(0, math.floor(cfg["interval_moving"])))
    end

    if cfg["interval_standing"] ~= nil then
        set_entry(OFF_ISTAND, id, math.max(0, math.floor(cfg["interval_standing"])))
    end

    if cfg["targets"] ~= nil then
        set_targets(id, cfg["targets"])
    end

    if cfg["range"] ~= nil then
        set_entry(OFF_RANGE, id, math.max(1, math.floor(cfg["range"])))
    end

    if cfg["wall_min_distance"] ~= nil then
        set_entry(OFF_WALLMIN, id, math.max(0, math.floor(cfg["wall_min_distance"])))
    end

    -- Behaviour once a siege tower has fixed itself to a wall and turned into
    -- the structure soldiers climb.
    if cfg["attached_interval"] ~= nil then
        set_entry(OFF_ATTINT, id, math.max(0, math.floor(cfg["attached_interval"])))
    end

    if cfg["attached_ignore_crew"] ~= nil then
        set_entry(OFF_ATTCREW, id, cfg["attached_ignore_crew"] == true and 1 or 0)
    end

    if cfg["attached_stop_when_boarded"] ~= nil then
        set_entry(OFF_ATTBOARD, id, cfg["attached_stop_when_boarded"] == true and 1 or 0)
    end

    if cfg["attached_board_radius"] ~= nil then
        local r = math.max(0, math.floor(cfg["attached_board_radius"]))
        set_entry(OFF_ATTBR2, id, r * r)
    end

    -- An AI lord whose character file permits cows sends one instead of a rock
    -- when the shot is aimed at troops.
    -- Keep the weapon loaded while idle and check often, so the shot goes off
    -- as soon as something walks into range.
    -- Aiming error applied to every projectile, including the first.
    -- Restrict everything this module does for the unit type to AI-owned units.
    if cfg["ai_only"] ~= nil then
        set_entry(OFF_AIONLY, id, cfg["ai_only"] == true and 1 or 0)
    end

    if cfg["inaccuracy"] ~= nil then
        set_entry(OFF_INACC, id, math.max(0, math.floor(cfg["inaccuracy"])))
    end

    if cfg["inaccuracy_tiles"] ~= nil then
        set_entry(OFF_INACC, id, math.max(0, math.floor(cfg["inaccuracy_tiles"] * 8)))
    end

    if cfg["preload"] ~= nil then
        set_entry(OFF_PRELOAD, id, cfg["preload"] == true and 1 or 0)
    end

    if cfg["preload_poll"] ~= nil then
        set_entry(OFF_PRELPOLL, id, math.max(1, math.floor(cfg["preload_poll"])))
    end

    if cfg["sync_to_animation"] ~= nil then
        set_entry(OFF_SYNC, id, cfg["sync_to_animation"] == true and 1 or 0)
    end

    if cfg["sync_max_wait"] ~= nil then
        set_entry(OFF_SYNCMAX, id, math.max(1, math.floor(cfg["sync_max_wait"])))
    end

    if cfg["ai_cow_vs_units"] ~= nil then
        set_entry(OFF_AICOW, id, cfg["ai_cow_vs_units"] == true and 1 or 0)
    end

    if cfg["density_min"] ~= nil then
        set_entry(OFF_DMIN, id, math.max(1, math.floor(cfg["density_min"])))
    end

    if cfg["density_radius"] ~= nil then
        set_entry(OFF_DRAD, id, math.max(1, math.floor(cfg["density_radius"])))
    end

    -- Staggering: stagger_max > 0 spreads a volley out instead of releasing it
    -- in one tick. The wait before each projectile is rolled per shot.
    if cfg["stagger_min"] ~= nil then
        set_entry(OFF_STAGMIN, id, math.max(0, math.floor(cfg["stagger_min"])))
    end

    if cfg["stagger_max"] ~= nil then
        local hi = math.max(0, math.floor(cfg["stagger_max"]))
        set_entry(OFF_STAGMAX, id, hi)
        -- A max on its own still needs a sane floor.
        if cfg["stagger_min"] == nil and hi > 0 then
            set_entry(OFF_STAGMIN, id, 1)
        end
    end

    if cfg["random_targets"] ~= nil then
        local on = cfg["random_targets"]
        set_entry(OFF_MULTI, id, (on == true or on == 1 or on == "true") and 1 or 0)
    end

    if cfg["shoot_height"] ~= nil then
        set_entry(OFF_HEIGHT, id, math.max(0, math.floor(cfg["shoot_height"])))
    end

    if cfg["require_manned"] ~= nil then
        local crew = cfg["require_manned"]
        if crew == true then crew = 1 elseif crew == false then crew = 0 end
        set_entry(OFF_MANNED, id, math.max(0, math.floor(crew)))
    end

    if cfg["suppress_default"] == true then
        set_entry(OFF_SUPPRESS, id, 1)
    end

    log(INFO, string.format("[projectileModifier] applied '%s' (type %d)", name, id))
end

namespace.apply = function(config)
    assert(not installed, '[projectileModifier] settings cannot be changed during a running session; relaunch the game')
    local validated = configuration.validate(config)
    if next(validated.units) == nil then return end
    install(validated)
    installed = true
end

namespace.enable = function(self, config)
    assert(not installed, '[projectileModifier] already enabled; relaunch to change settings')
    assert(type(config) == 'table', '[projectileModifier] expected module options')
    for key in pairs(config) do
        assert(key == 'projectile_config_file_selector' or key == 'customizations' or key == 'units',
            '[projectileModifier] unknown module option: ' .. tostring(key))
    end
    local path = config["projectile_config_file_selector"]
    local cfg = {units = config.units or {}}
    if path ~= nil and path ~= '' then
    assert(type(path) == 'string', '[projectileModifier] config path must be a string')
    assert(config.units == nil, '[projectileModifier] use either a file or inline units')
    local file = io.open(path, "rb")
    assert(file, '[projectileModifier] cannot open config file: ' .. tostring(path))
    local spec = file:read("*all")
    file:close()

---@diagnostic disable-next-line: undefined-global
    cfg = yaml.parse(spec)
    end
    namespace.apply(configuration.merge(cfg, config.customizations))
end

namespace.disable = function(self, config)
    if installed then return false, 'Projectile settings require a game restart' end
    return true
end

namespace.simulationStateFormat = 1
namespace.serializeSimulationState = function(self, handle)
    if persistent then persistent:serialize(handle) end
end

return namespace
