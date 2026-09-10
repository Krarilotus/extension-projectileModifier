-- Unit type ids are the index of the name in this list (Peasant == 1).
-- Identical to the list used by the rebalancer module.
local unit_names = {
    "Peasant", "Burning man", "Woodcutter", "Fletcher", "Tunneler", "Hunter",
    "Quarry mason", "Quarry grunt", "Quarry ox", "Pitch worker", "Wheat farmer",
    "Hops farmer", "Apple farmer", "Dairy farmer", "Miller", "Baker", "Brewer",
    "Poleturner", "Blacksmith", "Armourer", "Tanner",
    "European archer", "European crossbowman", "European spearman",
    "European pikeman", "European maceman", "European swordsman",
    "European knight", "Ladderman", "Engineer", "Iron miner1", "Iron miner2",
    "Priest", "Healer", "Drunkard", "Innkeeper", "Monk", "unknown1",
    "Catapult", "Trebuchet", "Mangonel", "Trader", "Trader horse", "Deer",
    "Lion", "Rabbit", "Camel", "Crow", "Seagull", "Siege tent", "Cow",
    "Hunter dog", "Fireman", "Ghost", "Lord", "Lady", "Jester", "Siege tower",
    "Battering ram", "Portable shield", "Tower ballista", "Chicken", "Mother",
    "Child", "Juggler", "Fireeater", "Dog", "unknown2", "unknown3",
    "Arabian archer", "Arabian slave", "Arabian slinger", "Arabian assassin",
    "Arabian horse archer", "Arabian swordsman", "Arabian firethrower",
    "Fire ballista"
}

-- Entity type ids accepted by the game's projectile spawner.
-- The rebalancer's projectile velocity/arc tables are indexed by (id - 1).
local projectile_names = {
    arrow                     = 1,
    catapult_rock             = 2,
    trebuchet_rock            = 3,
    mangonel_pebble           = 4,
    crossbow_bolt             = 7,
    ballista_bolt             = 20,
    cow                       = 23,
    arrow_untargeted           = 24,
    crossbow_bolt_untargeted   = 25,
    slinger_stone             = 33,
    firethrower_pot           = 34,
    slinger_stone_untargeted   = 35,
    firethrower_pot_untargeted= 36,
    fire_ballista_bolt        = 37,
    fire_arrow                = 91,
    fire_arrow_untargeted     = 92,
}

-- What a forced shooter is allowed to aim at, in the order the config lists them.
--   units          bounded nearest-enemy search using native team membership
--   walls          wall tiles near the shooter (tile layer, see the description for the caveat)
--   fortifications enemy gatehouses, towers, wooden gates, drawbridges, keep doors
--   buildings      every other enemy building
--   cluster        the tightest knot of enemies, if it is big enough
--   siege_towers   enemy siege towers fixed to a wall
local target_kinds = {
    units          = 1,
    walls          = 2,
    fortifications = 3,
    buildings      = 4,
    cluster        = 5,
    siege_towers   = 6,
}

-- Siege towers that have reached a wall and become the structure soldiers climb.
-- Confirmed as index 69 of the game's building update table, the slot whose
-- handler is UpdatePlacedSiegeTower. 83 is one still being pushed along.
local siege_tower_types = { 69 }

-- BuildingType ids that count as fortifications rather than plain buildings.
local fortification_types = {
    45, 46,             -- large / small gatehouse
    47, 48,             -- wooden gates
    49,                 -- drawbridge
    60, 61,             -- gatehouse, tower
    71, 72, 73,         -- keep doors
    74, 75, 76, 77, 78, -- tower one .. five
}

return {
    -- Native idle-state crew gates in the five siege update routines.
    native_reload_crews = {
        ['Catapult'] = 2, ['Trebuchet'] = 3, ['Mangonel'] = 2,
        ['Tower ballista'] = 2, ['Fire ballista'] = 2,
    },
    native_projectiles = {
        ['Hunter'] = 1, ['European archer'] = 1, ['European crossbowman'] = 7,
        ['Catapult'] = 2, ['Trebuchet'] = 3, ['Mangonel'] = 4,
        ['Tower ballista'] = 20, ['Arabian archer'] = 1,
        ['Arabian slinger'] = 33, ['Arabian horse archer'] = 1,
        ['Arabian firethrower'] = 36, ['Fire ballista'] = 37,
    },
    unit_names = unit_names,
    target_kinds = target_kinds,
    fortification_types = fortification_types,
    siege_tower_types = siege_tower_types,
    MAX_BUILDINGS = 2000,
    MAX_BUILDING_TYPES = 128,
    DEFAULT_RANGE = 20,
    DEFAULT_WALL_MIN_DISTANCE = 3,
    DEFAULT_DENSITY_RADIUS = 5,
    -- How close an enemy must be to count as standing on an attached structure.
    DEFAULT_BOARD_RADIUS = 2,
    -- AI character file layout: 169 fields of 4 bytes each, and the index the
    -- game stores per player is 1-based. Field 141 is CowThrowInterval.
    -- How often a unit holding a loaded weapon looks for something to shoot.
    DEFAULT_PRELOAD_POLL = 5,
    -- How long a ready shot waits for the animation before giving up on it.
    DEFAULT_SYNC_MAX_WAIT = 40,
    -- Largest micro coordinate on the map: 0x18F tiles of 8 micro units each.
    MAP_MICRO_MAX = 0x18F * 8,
    AIC_FIELD_COUNT = 169,
    AIC_COW_THROW_INTERVAL = 141,
    -- How soon a driven unit looks for a target again after finding none.
    RETRY_TICKS = 20,
    -- How many in-range enemies a random-target volley may choose between.
    -- Enough headroom that a density threshold in the tens is meaningful.
    MAX_CANDIDATES = 256,
    -- Ticks a unit keeps counting as "moving" after its last change of position.
    -- Slow units do not advance every tick, so without this they would flicker
    -- between the moving and standing intervals.
    MOVE_HYSTERESIS = 20,
    projectile_names = projectile_names,
    MAX_UNIT_TYPES = 80,
    UNIT_STRUCT_SIZE = 0x490,
    OFFSET_UNIT_TYPE = 0x8E,
}
