-- Runs in the standard ui module's LuaJIT state, as other native UCP menus do.
local choices, page = {}, 0
local rows = 8
local native_names = {english='Brazier',american='Brazier',german='Feuerkorb',
    french='Brasero',italian='Braciere',spanish='Brasero',polish='Koksownik'}
local native_name = native_names.english
local manager = remote.interface.manager
local menu_id = manager.getAvailableMenuID(2030)
local modal_id = manager.getAvailableModalMenuID(2031)
-- A modal can disappear before the game finishes processing its click. Consume
-- that input before entering build mode, or the map handles the same click too.
local reset_mouse = ffi.cast('void (__thiscall *)(void *)', remote.interface.core.AOBScan(
    '33 C0 39 81 D8 01 00 00 89 81 D8 01 00 00 75 ? 89 41 28 89 41 2C 89 41 30'))

remote.events.receive('custom-projectiles/decorations/open', function(_, value)
    choices = {{id=0,label=native_names[(value.language or 'english'):lower()] or native_name}}
    for _, choice in ipairs(value.choices) do choices[#choices+1] = choice end
    page = 0
end)

local function close()
    game.UI.activateModalMenu(game.UI.MenuModalComposition1, -1, false)
    reset_mouse(game.Input.mouseState)
end
local action = registerObject(ffi.cast('void (__cdecl *)(int)', function(parameter)
    if parameter==101 then page=math.max(0,page-1)
    elseif parameter==102 then page=math.min(math.floor((#choices-1)/rows),page+1)
    elseif parameter==103 then close()
    else
        local choice=choices[page*rows+parameter]
        if choice then
            close()
            remote.events.send('custom-projectiles/decorations/select', {id=choice.id})
        end
    end
end))
local render = registerObject(ffi.cast('void (__cdecl *)(int)', function(parameter)
    local label
    if parameter==101 then label=page>0 and '<' or ''
    elseif parameter==102 then label=(page+1)*rows<#choices and '>' or ''
    elseif parameter==103 then label='X'
    else local choice=choices[page*rows+parameter]; label=choice and choice.label or '' end
    if label=='' then return end
    local state=game.Rendering.ButtonState
    local old=game.Rendering.pDrawBufferChoiceValue[0]
    game.Rendering.pDrawBufferChoiceValue[0]=0
    game.Rendering.drawBlendedBlackBox(game.Rendering.pencilRenderCore,state.x,state.y,
        state.x+(parameter>100 and 48 or 440),state.y+28,0x14)
    game.Rendering.renderTextToScreenConst(game.Rendering.textManager,label,state.x+8,state.y+5,
        0,0xB8EEFB,0x12,0,0)
    game.Rendering.pDrawBufferChoiceValue[0]=old
end))
-- Native grouped buttons inherit callbacks from the preceding group header,
-- as in automarket. A callback on each grouped button alone is not sufficient.
local items={{menuItemType=0x01000000,
    menuItemActionHandler={address=tonumber(ffi.cast('unsigned long',action))},
    menuItemRenderFunction={address=tonumber(ffi.cast('unsigned long',render))}}}
local function button(parameter,x,y,width)
    items[#items+1]={menuItemType=0x02000003,menuItemRenderFunctionType=1,
        position={position={x=x,y=y}},itemWidth=width,itemHeight=28,
        callbackParameter={parameter=parameter}}
end
for row=1,rows do button(row,20,44+(row-1)*34,440) end
button(101,20,326,48);button(102,82,326,48);button(103,412,326,48)
items[#items+1]={menuItemType=0x66}
local menu=api.ui.Menu:createMenu({menuID=menu_id,
    menuItems=registerObject(ffi.new('MenuItem['..#items..']',items))})
local modal=api.ui.ModalMenu:createModalMenu({modalMenuID=modal_id,width=480,height=374,
    x=-1,y=-1,borderStyle=512,backgroundColor=0,menu=menu,
    menuModalRenderFunction=function(x,y,width,height)
        game.Rendering.drawBlendedBlackBox(game.Rendering.pencilRenderCore,x+6,y+6,x+width-6,y+height-6,0x14)
        game.Rendering.renderTextToScreenConst(game.Rendering.textManager,'Custom Projectiles',x+20,y+18,
            0,0xCCFAFF,0xF,0,0)
        game.Rendering.renderTextToScreenConst(game.Rendering.textManager,
            tostring(page+1)..' / '..tostring(math.max(1,math.ceil(#choices/rows))),x+210,y+334,
            0,0xB8EEFB,0x12,0,0)
    end})
registerObject(menu);registerObject(modal)
return {modal=modal_id}
