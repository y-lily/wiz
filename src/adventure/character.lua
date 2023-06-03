package.path = package.path .. ";./res/?.lua;./?.lua;./wiz/res/?.lua"

---@class Trigger
local Trigger = require "trigger"

---@class Character
---@field name string
---@field entity Entity
---@field state string
---@field position _2D
---@field defined_states table
---@field trigger Trigger
local Character = {}

---@class char_def
---@field name string
---@field entity Entity
---@field state string
---@field position _2D
---@field defined_states table
---@field trigger Trigger

---@type fun(self: Character, def: char_def): Character
function Character:new(def)
    -- Required fields.
    assert(def.name)
    assert(def.entity)
    assert(def.state)
    assert(def.defined_states)
    assert(def.position)

    local this = {
        name = def.name,
        entity = def.entity,
        state = def.state,
        defined_states = def.defined_states,
        position = def.position,
        trigger = def.trigger or Trigger:new({}),
    }

    setmetatable(this, self)
    return this
end

return Character
