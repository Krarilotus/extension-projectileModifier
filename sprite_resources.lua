-- Complete native-format sheets; pixels stay owned by gmResourceModifier.
local constants = require('constants')
local M = {}
M.sheets = {
    [34]={count=184, kind=2, name='body_missile'},
    [122]={count=144, kind=2, name='body_missile_2'},
    [135]={count=29, kind=2, name='body_missile_cow'},
    [138]={count=8, kind=6, name='body_brazier'},
    [145]={count=144, kind=2, name='body_missile_fire'},
    [158]={count=32, kind=1, name='rock_chips'},
}
M.projectile_gm = {}
for name, id in pairs(constants.projectile_names) do
    local gm = 34
    if name:find('ballista') then gm = 122
    elseif name == 'cow' then gm = 135
    elseif name:find('fire_arrow') then gm = 145
    elseif name:find('slinger') or name:find('firethrower') then gm = 158 end
    M.projectile_gm[id] = gm
end
local function check(ok, message)
    assert(ok, '[custom-projectiles] sprites: ' .. message)
end

function M.definitions(input)
    if input==nil then return {} end
    check(type(input)=='table', 'projectiles must be a mapping')
    local names, result = {}, {}
    for name in pairs(input) do
        check(type(name)=='string' and #name<=48 and name:match('^[a-z][a-z0-9_%-]*$')
            and not constants.projectile_names[name], 'use a unique lowercase variant name (max 48 characters)')
        names[#names+1]=name
    end
    table.sort(names)
    check(#names<=33, 'at most 33 named variants are supported')
    for index,name in ipairs(names) do
        local spec=input[name]
        check(type(spec)=='table', name .. ' must be a mapping')
        for key in pairs(spec) do
            check(key=='inherits' or key=='sprites', name .. ': unknown setting ' .. tostring(key))
        end
        local base=constants.projectile_names[spec.inherits]
        check(base~=nil, name .. ': inherits must name a native projectile')
        local path=spec.sprites
        check(type(path)=='string' and #path>4 and #path<=240 and path:lower():sub(-4)=='.gm1'
            and not path:find('[%z\1-\31]'), name .. ': sprites must be a GM1 path relative to the game folder')
        path=path:gsub('\\','/')
        check(path:sub(1,1)~='/' and not path:find(':') and not ('/'..path..'/'):find('/%.%./'),
            name .. ': use a relative path without parent traversal')
        result[name]={id=256+index, base=base, gm=M.projectile_gm[base], path=path}
    end
    return result
end

function M.prepare(definitions, decorations)
    local resources, assets = {}, {}
    local function add(name, spec, decoration)
        if not spec.path then return end
        local key=spec.gm .. ':' .. spec.path
        if not assets[key] then
            assets[key]={path=spec.path, gm=spec.gm, names={}, decorations={}}
            resources[#resources+1]=assets[key]
        end
        local asset=assets[key]
        local names = decoration and asset.decorations or asset.names
        names[#names+1]=name
    end
    for name, spec in pairs(definitions) do add(name, spec, false) end
    for name, spec in pairs(decorations or {}) do add(name, spec, true) end
    check(#resources<=33, 'projectile and decoration sheets share at most 33 free GM slots')
    table.sort(resources,function(a,b) return a.gm==b.gm and a.path<b.path or a.gm<b.gm end)
    if #resources==0 then return resources end
    local modifier=assert(modules.gmResourceModifier, '[custom-projectiles] gmResourceModifier is required for custom sprites')
    check(modifier.LoadCompleteGm1Resource and modifier.ReserveGm and modifier.GetReservedGm and modifier.FreeGm1Resource,
        'gmResourceModifier 0.3.1 is required for complete inherited sprite sheets')
    local loaded={}
    local ok, err=pcall(function()
        for _,asset in ipairs(resources) do
            local sheet=assert(M.sheets[asset.gm], 'unsupported base sheet')
            local resource, hash=modifier:LoadCompleteGm1Resource(asset.path,sheet.count,sheet.kind)
            if type(resource)=='number' and resource>=0 then loaded[#loaded+1]=resource end
            check(type(resource)=='number' and resource>=0 and type(hash)=='string' and
                #hash==64 and hash:match('^[0-9a-f]+$'), 'failed to load or validate '..asset.path)
            asset.resource, asset.hash=resource,hash
            for _,name in ipairs(asset.names) do definitions[name].sha256=hash end
            for _,name in ipairs(asset.decorations) do decorations[name].sha256=hash end
        end
    end)
    if not ok then
        for _,resource in ipairs(loaded) do modifier:FreeGm1Resource(resource) end
        error(err)
    end
    return resources
end

-- Sheet admission and resource lifetime belong to gmResourceModifier. No
-- consumer loader hook or native metadata allocation is installed here.
function M.install(resources, bind)
    if #resources==0 then return end
    local modifier=assert(modules.gmResourceModifier, '[custom-projectiles] gmResourceModifier is required for custom sprites')
    check(modifier.ReserveGm and modifier.GetReservedGm,
        'gmResourceModifier 0.3.1 is required for inherited sprite sheets')
    for _,asset in ipairs(resources) do
        asset.reservation=modifier:ReserveGm(asset.gm,asset.resource)
        check(asset.reservation>=0, 'failed to reserve '..asset.path)
    end
    hooks.registerHookCallback('afterInit',function()
        -- Resolve the complete result before exposing any variant. Ordinary
        -- errors in afterInit are caught; the framework fatal logger terminates.
        for _,asset in ipairs(resources) do
            asset.slot=modifier:GetReservedGm(asset.reservation)
            if asset.slot<0 then
                log(FATAL, '[custom-projectiles] Required custom sprite sheets were not admitted by gmResourceModifier. Check their inherited layouts and available sheet/image capacity.')
                return
            end
        end
        for _,asset in ipairs(resources) do bind(asset) end
    end)
end
return M
