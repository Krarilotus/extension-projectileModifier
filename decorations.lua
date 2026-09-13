-- Build-menu choices use native brazier placement and a lockstep payload.
local M = {}
local function check(ok, message)
    assert(ok, '[custom-projectiles] decorations: '..message)
end

function M.definitions(input)
    if input==nil then return {} end
    check(type(input)=='table', 'expected a mapping')
    local names,result={},{}
    for name in pairs(input) do
        check(type(name)=='string' and #name<=48 and name:match('^[a-z][a-z0-9_%-]*$'),
            'use lowercase decoration names of at most 48 characters')
        names[#names+1]=name
    end
    table.sort(names)
    check(#names<=33,'at most 33 decoration types are supported')
    for id,name in ipairs(names) do
        local spec=input[name]
        check(type(spec)=='table',name..' must be a mapping')
        for key in pairs(spec) do check(key=='label' or key=='sprites',name..': unknown setting '..tostring(key)) end
        local label=spec.label or name
        check(type(label)=='string' and #label>=1 and #label<=96 and not label:find('[%z\1-\31]'),
            name..': label must be a short printable string')
        local path=spec.sprites
        if path~=nil then
            check(type(path)=='string' and #path>4 and #path<=240 and path:lower():sub(-4)=='.gm1',
                name..': sprites must be a GM1 path relative to the game folder')
            path=path:gsub('\\','/')
            check(path:sub(1,1)~='/' and not path:find('[:%z\1-\31]') and not ('/'..path..'/'):find('/%.%./'),
                name..': use a relative path without parent traversal')
        end
        result[name]={id=id,label=label,path=path,gm=138}
    end
    return result
end

-- A list gives an explicit, stable precedence. The first nearby match wins.
-- Fortification overrides apply first; then this rule's sparse fields apply.
function M.rules(input, definitions, unit_name)
    if input==nil then return {} end
    check(type(input)=='table',unit_name..'.near_decorations must be a list')
    local count,seen,result=0,{},{}
    for key in pairs(input) do
        check(type(key)=='number' and key%1==0 and key>=1 and key<=#input,
            unit_name..'.near_decorations must be a list')
        count=count+1
    end
    check(count==#input and count<=33,'at most 33 rules per unit are supported')
    for priority,rule in ipairs(input) do
        check(type(rule)=='table',unit_name..': expected a rule mapping')
        local name=rule.decoration
        check(definitions[name] and not seen[name],unit_name..': unknown or repeated decoration')
        seen[name]=true
        local fields={}
        for key,value in pairs(rule) do
            if key~='decoration' then
                check(key~='near_decorations' and key~='on_fortification',unit_name..': nested trigger rules are unsupported')
                fields[key]=value
            end
        end
        check(next(fields)~=nil,unit_name..': a decoration rule needs at least one projectile setting')
        result[#result+1]={name=name,id=definitions[name].id,priority=priority,fields=fields}
    end
    return result
end

-- Native brazier clicks use entity command 69, not building command 28.
-- Carry microtile coordinates (8 per tile) and the variant through lockstep;
-- derive ownership, valid height and price from synchronized game state.
function M.valid_placement(context, by_id)
    if type(context)~='table' then return false end
    for _,key in ipairs({'x','y','decoration'}) do
        local n=context[key]
        if type(n)~='number' or n%1~=0 then return false end
    end
    return context.x>=0 and context.x<3200 and context.y>=0 and context.y<3200
        and by_id[context.decoration]~=nil
end

function M.protocol(by_id, invoker, place)
    return {
        schedule=function(self,meta,context)
            check(M.valid_placement(context,by_id),'invalid placement request')
            meta.parameters:serializeInteger(context.x)
            meta.parameters:serializeInteger(context.y)
            meta.parameters:serializeInteger(context.decoration)
        end,
        scheduleAfterReceive=function() end,
        execute=function(self,meta)
            local context={x=meta.parameters:deserializeInteger(),y=meta.parameters:deserializeInteger(),
                decoration=meta.parameters:deserializeInteger()}
            local player=invoker()
            if type(player)~='number' or player<1 or player>8 or player%1~=0 then return end
            if not M.valid_placement(context,by_id) then return end
            place(player,context.x,context.y,context.decoration)
        end,
    }
end

function M.resolve(locate)
    local command=locate('A1 ? ? ? ? 83 EC 08 83 F8 01 C7 05 ? ? ? ? 09 00 00 00 0F 85 ? ? ? ? 6A 00 50 50')
    local function relative(offset)
        check(core.readByte(command+offset)==0xE8,'unsupported entity dispatcher')
        return (command+offset+5+core.readInteger(command+offset+1))%4294967296
    end
    local near=locate('53 55 56 57 8B D9 BF 01 00 00 00 39 7B 04 7E 62')
    local click=locate('6A 45 B9 ? ? ? ? 89 2D ? ? ? ? 89 3D ? ? ? ? E8 ? ? ? ? 5E 5F 5D 5B 83 C4 08 C3')
    local queue=(click+24+core.readInteger(click+20))%4294967296
    -- UCP returns signed int/short values; compare opcode bit patterns modulo
    -- their width so signatures containing high bits work in the live runtime.
    check(core.readInteger(queue)%4294967296==0xF18B5653 and core.readSmallInteger(queue+4)%65536==0x868B,
        'unsupported native command queue')
    check(core.readByte(near+0x27)==0x66 and core.readByte(near+0x2C)==0x37,
        'unsupported native proximity loop')
    local validation=locate('8B 44 24 04 66 83 3C 45 ? ? ? ? 00 75 05 33 C0 C2 08 00')
    local height=locate('56 57 8B 7C 24 0C 8B F1 0F BF 84 7E B0 29 20 00 85 C0')
    local funds=locate('69 D2 F4 39 00 00 3B 8A ? ? ? ? 7E 09 33 FF')
    return {
        command=command, commandID=69, spawn=relative(0x190), cost=relative(0x1BD), debit=relative(0x1D7),
        entityState=core.readInteger(command+0x18C), buildings=core.readInteger(command+0x1B9),
        invoker=core.readInteger(command+0x1DE), controlling=core.readInteger(command+0x1E4),
        gameMode=core.readInteger(command+0x197), gold=core.readInteger(funds+8),
        x=core.readInteger(command+0x35), y=core.readInteger(command+0x4A),
        kind=core.readInteger(command+0x74), queue=queue, valid=validation, height=height,
        action=locate('53 33 DB 39 1D ? ? ? ? 0F 85 ? ? ? ? 39 1D ? ? ? ? 0F 85 ? ? ? ? A1 ? ? ? ? 8B C8'),
        filter=near+0x27, filterResume=near+0x2D, filterNext=near+0x64,
    }
end

function M.install(definitions, native, values, open_menu)
    local by_id={}
    for _,spec in pairs(definitions) do by_id[spec.id]=spec end
    local protocol=assert(modules.protocol,'[custom-projectiles] protocol is required for decorations')
    local spawn=core.exposeCode(native.spawn,12,1)
    local valid=core.exposeCode(native.valid,3,1)
    local height=core.exposeCode(native.height,2,1)
    local cost=core.exposeCode(native.cost,4,1)
    local debit=core.exposeCode(native.debit,5,1)
    local rebuild=core.exposeCode(values.REBUILDDECOR,0,0)
    local cost_buffer=core.allocate(8)
    local tilemap=values.TILEFLAGS-0x165160
    local function execute(player,x,y,variant)
        local tile=core.readInteger(values.TILEROWS+math.floor(y/8)*12)+math.floor(x/8)
        -- The same predicate used by the native brazier build cursor includes
        -- wall/tower ownership, edge clearance and existing obstructions.
        if valid(tilemap,tile,player)==0 then return end
        local price=0
        if core.readInteger(native.gameMode)==6 then
            cost(native.buildings,148,cost_buffer,cost_buffer+4)
            price=core.readInteger(cost_buffer+4)
            if core.readInteger(native.gold+player*0x39F4)<price then return end
        end
        local z=height(tilemap,tile)
        local id=spawn(native.entityState,0,player,0,x,y,z,x,y,z,14,0)
        if id<1 or id>=3000 then return end
        local entity=values.ENTITYARRAY+id*232
        if core.readSmallInteger(entity+0x2A)~=14 then return end
        core.writeInteger(values.DECORVARIANT+id*4,variant)
        core.writeInteger(values.DECORUID+id*4,core.readInteger(entity+0x30))
        local gm=core.readInteger(values.DECORGM+variant*4)
        if gm>0 then core.writeSmallInteger(entity+6,gm) end
        if price>0 then debit(native.buildings,player,15,price,0) end
        rebuild()
    end
    local number=protocol:registerCustomProtocol('custom-projectiles','place-decoration','LOCKSTEP',12,
        M.protocol(by_id,function() return core.readInteger(native.invoker) end,execute))
    local selected=0
    local original_queue
    original_queue=core.hookCode(function(this,command)
        if command==native.commandID and selected~=0 and core.readInteger(native.kind)==14 then
            local context={x=core.readInteger(native.x),y=core.readInteger(native.y),decoration=selected}
            if M.valid_placement(context,by_id) then protocol:invokeProtocol(number,context) end
            return 0
        end
        return original_queue(this,command)
    end,native.queue,2,1,10)
    local original_action
    original_action=core.hookCode(function(parameter)
        selected=0
        if parameter==148 then open_menu();return 0 end
        return original_action(parameter)
    end,native.action,1,0,9)
    return function(variant)
        check(variant==0 or by_id[variant],'unknown decoration choice')
        original_action(148)
        selected=variant
    end
end
return M
