class GameObject:
    #A generic object. Always represented by a character on screen.
    def __init__(self, x, y, char, name, color, my_map, objects, blocks=False):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.my_map = my_map
        self.objects = objects

    def move(self, dx, dy):
        if not self.is_blocked(self.x + dx, self.y + dy, self.my_map, self.objects):
            self.x += dx
            self.y += dy

    def draw(self, con, vis_tiles):
        if(self.x, self.y) in vis_tiles:
            con.draw_char(self.x, self.y, self.char, self.color, bg=None)

    def clear(self, con):
        con.draw_char(self.x, self.y, ' ', self.color, bg=None)

    def is_blocked(self, x, y, my_map, objects):
        if my_map[x][y].blocked:
            return True

        for obj in objects:
            if obj.blocks and obj.x == x and obj.y == y:
                return True

        return False
