package.path = package.path .. ";./res/?.lua;./?.lua;./wiz/res/?.lua"

---@class Trigger
local Trigger = {}

local no_op = function() end

---@param def table
---@return table
function Trigger:new(def)
    local this = {
        onEnter = def.onEnter or no_op,
        onExit = def.onExit or no_op,
        onUse = def.onUse or no_op,
    }

    setmetatable(this, self)
    return this
end

return Trigger
