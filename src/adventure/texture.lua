package.path = package.path .. ";./res/?.lua;./?.lua;./wiz/res/?.lua"

---@class Texture
local Texture = {}


---@param def table
---@return table
function Texture:new(def)
    -- Required fields.
    assert(def.size)
    assert(def.part_size)
    local this = {
        size = def.size,
        part_size = def.part_size,
        source = def.source,
        alpha = def.alpha or false,
        parts = def.parts or {
            topleft = 0,
            top = 1,
            topright = 2,
            left = 3,
            center = 4,
            right = 5,
            bottomleft = 6,
            bottom = 7,
            bottomright = 8,
        }
    }

    setmetatable(this, self)
    return this
end

return Texture
