package.path = package.path .. ";./res/?.lua;./?.lua;./wiz/res/?.lua"

---@class Character
local Character = {}

---@param def table
---@return table
function Character:new(def)

    local this = {
        ---@type string
        name = def.name,
        ---@type Entity
        entity = def.entity,
        ---@type string
        state = def.state,
        ---@type table
        defined_states = def.defined_states,
        ---@type table
        position = def.position,
        ---@type Trigger
        trigger = def.trigger or Trigger:new({}),
    }

    -- Required fields.
    assert(this.name)
    assert(this.entity)
    assert(this.state)
    assert(this.defined_states)

    setmetatable(this, self)
    return this
end

return Character
