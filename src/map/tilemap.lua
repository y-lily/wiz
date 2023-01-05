---@class Object
local Object = require "classic"
---@class Tilemap : Object
local Tilemap = Object:extend()

function Tilemap:new(map_data)
    self.image = love.graphics.newImage(map_data.tilesets[1].name .. ".png")
    self.tileWidth = map_data.tilewidth
    self.tileHeight = map_data.tileheight
    self.map = map_data.layers[1].data
    self.uvs = {}
    self.quads = {}
    self.drawable = {
        x = 1,
        y = 1,
        width = 0,
        height = 0
    }
    self.wx = 0
    self.wy = 0
    self:_updateUVs()
    self:_setupQuads()
    self:_splitMap(map_data.layers[1].width)
end

---Update drawable info.
---@param x? number              number of the first column in the map
---@param y? number              number of the first row in the map
---@param width? integer         number of columns to draw
---@param height? integer        number of rows to draw
function Tilemap:updateDrawable(x, y, width, height)
    self.drawable.x = x or self.drawable.x
    self.drawable.y = y or self.drawable.y
    self.drawable.width = width or self.drawable.width
    self.drawable.height = height or self.drawable.height
end

---@param wx? number
---@param wy? number
function Tilemap:draw(wx, wy)
    if (wx ~= nil and wx ~= self.wx) or (wy ~= nil and wy ~= self.wy) then
        self.wx = wx or self.wx
        self.wy = wy or self.wy
        self:_updateUVs()
    end

    local window_width, window_height = love.graphics.getDimensions()

    for j = 0, self.drawable.height - 1 do
        local vs = self.uvs[j + 1]
        local v = vs[1].v
        if v > window_height then return end -- Don't draw off screen.
        local row = self.map[self.drawable.y + j]
        if row == nil then goto continue end -- Skip non-present rows but don't abort in case we deal with negative indices.

        for i = 0, self.drawable.width - 1 do
            local u = vs[i + 1].u
            if u > window_width then break end -- Don't draw columns off screen.
            local tile = row[self.drawable.x + i]
            local quad = self.quads[tile]
            if quad ~= nil then
                love.graphics.draw(self.image, quad, u, v)
            end
        end

        ::continue::
    end
end

function Tilemap:_updateUVs()
    self.uvs = {}

    local max_width, max_height = love.window.getDesktopDimensions()

    for j = 0 + self.wy, max_height, self.tileHeight do
        local row = {}
        for i = 0 + self.wx, max_width, self.tileWidth do
            local uv = {
                u = i,
                v = j
            }
            table.insert(row, uv)
        end
        table.insert(self.uvs, row)
    end
end

function Tilemap:_setupQuads()
    local width = math.floor(self.image:getWidth() / self.tileWidth)
    local height = math.floor(self.image:getHeight() / self.tileHeight)
    self.quads = {}

    for j = 0, height - 1 do
        for i = 0, width - 1 do
            local quad = love.graphics.newQuad(i * self.tileWidth, j * self.tileHeight,
                self.tileWidth, self.tileHeight,
                self.image:getDimensions())
            table.insert(self.quads, quad)
        end
    end
end

function Tilemap:_splitMap(map_width)
    if type(self.map[1]) == "table" or map_width == nil or map_width < 1 then
        return
    end

    local new_map = {}
    for i = 1, #self.map, map_width do
        local row = { unpack(self.map, i, i + map_width - 1) }
        table.insert(new_map, row)
    end

    self.map = new_map
end

return Tilemap
