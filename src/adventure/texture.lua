package.path = package.path .. ";./res/?.lua;./?.lua;./wiz/res/?.lua"

---@class Texture
local Texture = {}


---@param def table
---@return table
function Texture:new(def)
    local this = {
        width = def.width,
        height = def.height,
        source = def.source,
        alpha = def.alpha or false,
        part_width = def.part_width,
        part_height = def.part_height,
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

    assert(this.width)
    assert(this.height)
    assert(this.source)
    assert(this.part_width)
    assert(this.part_height)
    setmetatable(this, self)
    return this
end

return Texture
