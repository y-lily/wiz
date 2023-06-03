package.path = package.path .. ";./res/?.lua;./?.lua;./wiz/res/?.lua"

---@class Trigger
---@field onEnter function<any, any>
---@field onExit function<any, any>
---@field onUse function<any, any>
local Trigger = {}

---@class trigger_def
---@field onEnter function<any, any>
---@field onExit function<any, any>
---@field onUse function<any, any>

local no_op = function() end

---@type fun(self: Trigger, def: trigger_def): Trigger
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
