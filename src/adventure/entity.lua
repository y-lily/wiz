package.path = package.path .. ";./res/?.lua;./?.lua;./wiz/res/?.lua"

---@class Entity
local Entity = {}

local DEFAULT_FRAMERATE = 30


---@param def table
---@return table
function Entity:new(def)

    local this = {
        ---@type string
        source = def.source,
        ---@type boolean
        alpha = def.alpha or true,
        ---@type integer
        framewidth = def.framewidth,
        ---@type integer
        frameheight = def.frameheight,
        ---@type string
        flip = def.flip or "right-left",
        ---@type integer
        framerate = def.framerate or DEFAULT_FRAMERATE,
        ---@type string
        face_direction = def.face_direction or "down",
        ---@type integer
        frame = def.frame or 0,
        ---@type integer
        movement_speed = def.movement_speed,
        ---@type table
        animations = def.animations,
    }

    -- Required fields.
    assert(this.source)
    assert(this.framewidth)
    assert(this.frameheight)
    assert(this.movement_speed)
    assert(this.animations)

    setmetatable(this, self)
    return this
end

return Entity
