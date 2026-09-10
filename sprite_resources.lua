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
local function u32(s, off) return string.unpack('<I4', s, off+1) end
local function u16(s, off) return string.unpack('<I2', s, off+1) end

function M.validate_gm1(bytes, gm)
    local sheet = assert(M.sheets[gm], 'unsupported base sheet')
    check(type(bytes)=='string' and #bytes>=5208, 'truncated GM1 header')
    local count, kind, size = u32(bytes,12), u32(bytes,20), u32(bytes,80)
    check(count==sheet.count and kind==sheet.kind,
        'expected complete ' .. sheet.name .. '.gm1 layout (' .. sheet.count .. ' images, type ' .. sheet.kind .. ')')
    local pixels = 5208 + count*24
    check(size<=16777216 and #bytes==pixels+size, 'invalid GM1 data size')
    for index=0,count-1 do
        local offset = u32(bytes,5208+index*4)
        local length = u32(bytes,5208+count*4+index*4)
        local header = 5208+count*8+index*16
        local width, height = u16(bytes,header), u16(bytes,header+2)
        check(bytes:sub(header+9,header+16)==string.rep('\0',8),
            'projectile frames must be self-contained; linked/tiled image metadata is unsupported')
        check(width>0 and height>0 and width<=2048 and height<=2048, 'invalid image dimensions')
        check(length>0 and offset+length<=size, 'image data exceeds GM1 payload')
        -- Validate token and pixel bounds before the native decoder/converter
        -- touches user data. Animations store palette indices, type 1 RGB555.
        local p, finish, x, y = pixels+offset+1, pixels+offset+length, 0, 0
        local pixel_size = kind==2 and 1 or 2
        while p<=finish do
            local token=bytes:byte(p); p=p+1
            local flag, run=token//32, token%32+1
            if flag==4 then
                -- Native sheets align each stream to four bytes with up to
                -- three extra newline tokens after the declared last row.
                check(y<height or (token==128 and finish-p+1<=2), 'invalid image padding')
                y=y+1; x=0
                check(y<=height+3, 'too many image rows')
            else
                check(flag==0 or flag==1 or flag==2, 'unsupported image token')
                check(y<height and x+run<=width, 'image run exceeds dimensions')
                x=x+run
                if flag==0 then p=p+run*pixel_size
                elseif flag==2 then p=p+pixel_size end
                check(p<=finish+1, 'truncated image pixels')
            end
        end
        check(y>=height or (y==height-1 and x==width), 'incomplete image rows')
    end
    return {count=count, kind=kind, size=size}
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
            local file=assert(io.open(spec.path,'rb'), '[custom-projectiles] cannot open sprite sheet: '..spec.path)
            local bytes=file:read(16777216+5208+184*24+1); file:close()
            M.validate_gm1(bytes,spec.gm)
            check(sha and sha.sha256, 'framework SHA256 service is unavailable')
            assets[key]={path=spec.path, gm=spec.gm, hash=sha.sha256(bytes), names={}, decorations={}}
            resources[#resources+1]=assets[key]
        end
        local asset=assets[key]
        local names = decoration and asset.decorations or asset.names
        names[#names+1]=name
        spec.sha256=asset.hash
    end
    for name, spec in pairs(definitions) do add(name, spec, false) end
    for name, spec in pairs(decorations or {}) do add(name, spec, true) end
    check(#resources<=33, 'projectile and decoration sheets share at most 33 free GM slots')
    table.sort(resources,function(a,b) return a.gm==b.gm and a.path<b.path or a.gm<b.gm end)
    return resources
end

-- Called inside the real GM loader, before gmResourceModifier snapshots the
-- headers and initializes its replacers. Validate the entire reservation first.
function M.clone(resources, renderer, addresses, bind)
    local first=core.readInteger(renderer+0x4C)
    local next_image=core.readInteger(renderer+0x48)
    check(first>=1 and first+#resources<=240, 'no free GM slots remain')
    local sum=1
    for gm=0,239 do
        local count=core.readInteger(renderer+0x51C+gm*5208+12)
        check(count<=66000, 'corrupt native image count')
        if gm>=first then check(count==0, 'GM slot already owned by another extension') end
        sum=sum+count
    end
    check(sum==next_image and next_image<=66000, 'native image layout is incompatible')
    local cursor=next_image
    for i,asset in ipairs(resources) do
        local spec=M.sheets[asset.gm]
        local header=renderer+0x51C+asset.gm*5208
        check(core.readInteger(header+12)==spec.count and core.readInteger(header+20)==spec.kind,
            'base sheet was changed incompatibly by another extension')
        local source=core.readInteger(addresses.first+asset.gm*4)
        check(source>=1 and source+spec.count<=next_image, 'invalid native sheet offset')
        asset.slot=first+i-1; asset.first=cursor; asset.source=source
        cursor=cursor+spec.count
    end
    check(cursor<=66000, 'custom sheets exceed the 66000-image capacity')
    local function copy(to,from,length) core.writeBytes(to,core.readBytes(from,length)) end
    for _,asset in ipairs(resources) do
        local count=M.sheets[asset.gm].count
        copy(renderer+0x51C+asset.slot*5208,renderer+0x51C+asset.gm*5208,5208)
        for _,item in ipairs({{addresses.headers,16},{addresses.offsets,4},{addresses.sizes,4}}) do
            copy(item[1]+asset.first*item[2],item[1]+asset.source*item[2],count*item[2])
        end
        core.writeInteger(addresses.first+asset.slot*4,asset.first)
        bind(asset)
    end
    core.writeInteger(renderer+0x48,cursor)
    core.writeInteger(renderer+0x4C,first+#resources)
    core.writeInteger(addresses.count,first+#resources)
end

function M.install(resources, locate, bind)
    if #resources==0 then return end
    local modifier=assert(modules.gmResourceModifier, '[custom-projectiles] gmResourceModifier is required for custom sprites')
    local loader=locate('53 55 8B 6C 24 0C 56 57 8B D9')
    local addresses={
        first=core.readInteger(loader+0x72), count=core.readInteger(loader+0x36),
        headers=core.readInteger(locate('C1 E0 04 81 C1 ? ? ? 00 50 51')+5),
        sizes=core.readInteger(locate('89 14 BD ? ? ? 00 EB 53')+3),
        offsets=core.readInteger(locate('8B 2C BD ? ? ? 00 03 D7 3B FA')+3),
    }
    check(core.readByte(loader+0x6F)==0x89 and core.readByte(loader+0x35)==0xA3, 'unsupported GM loader')
    for _,asset in ipairs(resources) do
        asset.resource=modifier:LoadGm1Resource(asset.path)
        check(type(asset.resource)=='number' and asset.resource>=0, 'failed to load '..asset.path)
    end
    local original, initialized
    original=core.hookCode(function(renderer, filenames)
        check(not initialized, 'GM loader unexpectedly ran twice')
        original(renderer,filenames)
        M.clone(resources,renderer,addresses,function(asset)
            check(modifier:SetGm(asset.slot,-1,asset.resource,-1), 'failed to queue '..asset.path)
            bind(asset)
        end)
        initialized=true
    end,loader,2,1,6)
end
return M
