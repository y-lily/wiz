package.path = package.path .. ";./res/?.lua;./?.lua;./wiz/res/?.lua"

local DEFAULT_FRAMERATE = 30

---@class Entity
---@field source string
---@field alpha boolean
---@field framewidth integer
---@field frameheight integer
---@field flip string
---@field face_direction string
---@field framerate integer
---@field frame integer
---@field movement_speed integer
---@field animations table
local Entity = {}

---@class entity_def
---@field source string
---@field alpha boolean
---@field framewidth integer
---@field frameheight integer
---@field flip string
---@field face_direction string
---@field framerate integer
---@field frame integer
---@field movement_speed integer
---@field animations table


---@type fun(self: Entity, def: entity_def): Entity
function Entity:new(def)
    -- Required fields.
    assert(def.source)
    assert(def.framewidth)
    assert(def.frameheight)
    assert(def.movement_speed)
    assert(def.animations)

    local this = {
        source = def.source,
        alpha = def.alpha or true,
        framewidth = def.framewidth,
        frameheight = def.frameheight,
        flip = def.flip or "right-left",
        framerate = def.framerate or DEFAULT_FRAMERATE,
        face_direction = def.face_direction or "down",
        frame = def.frame or 0,
        movement_speed = def.movement_speed,
        animations = def.animations,
    }

    setmetatable(this, self)
    return this
end

return Entity
