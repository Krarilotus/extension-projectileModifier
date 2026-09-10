-- Keep configuration in YAML. This menu only selects what the player builds.
local M = {}
function M.prepare(definitions)
    local ui = assert(modules.ui, '[custom-projectiles] ui is required for decorations')
    local menu = ui:createMenuFromFile('ucp/modules/custom-projectiles/ui/decorations.lua', true, true)
    assert(type(menu)=='table' and type(menu.modal)=='number', '[custom-projectiles] decoration menu failed to load')
    local choices = {}
    for _, spec in pairs(definitions) do choices[spec.id] = {id=spec.id,label=spec.label} end
    local select
    ui:registerEventHandler('custom-projectiles/decorations/select', function(_, value)
        if select and type(value)=='table' and type(value.id)=='number'
            and (value.id==0 or choices[value.id]) then select(value.id) end
    end)
    return function()
        -- cr.tex is loaded after module initialization; read language on opening.
        local language = data.version.getGameLanguage and data.version.getGameLanguage() or 'english'
        ui:sendEvent('custom-projectiles/decorations/open', {choices=choices,language=language})
        ui:activateModalMenu(menu.modal, 1, 0)
    end, function(callback) select=callback end
end
return M
