import math

class GameObject:
    #A generic object. Always represented by a character on screen.
    def __init__(self, x, y, char, name, color, my_map, objects, blocks=False, fighter=None, ai=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.my_map = my_map
        self.objects = objects
        self.fighter = fighter

        if self.fighter:
            self.fighter.owner = self

        self.ai = ai
        if self.ai:
            self.ai.owner = self

    def move(self, dx, dy):
        if not self.is_blocked(self.x + dx, self.y + dy, self.my_map, self.objects):
            self.x += dx
            self.y += dy

    def move_or_attack(self, dx, dy, objects):
        x = self.x + dx
        y = self.y + dy

        target = None
        for obj in objects:
            if obj.x == x and obj.y == y and obj.fighter:
                target = obj
                break
        if target is not None:
            self.fighter.attack(target)
        else:
            self.move(dx, dy)

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

    def move_towards(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        #normalize it to length 1 (preserving direction) then round it and
        #convert to int so the movement is restricted to the grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def send_to_back(self, objects):
        objects.remove(self)
        objects.insert(0, self)

class Fighter:
    #Combat-related properties and methods
    def __init__(self, hp, defense, strength, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.strength = strength
        self.death_function = death_function

    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            func = self.death_function
            if func is not None:
                func(self.owner)

    def attack(self, target):
        damage = self.strength - target.fighter.defense

        if damage > 0:
            message(self.owner.name.capitalize() + ' smacks ' + target.name + ' for ' + str(damage) + ' damage.')
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize() + ' bludgeons ' + target.name + ' but whiffs!')


class BasicMonster():
    #AI for a basic monster
    def take_turn(self, visible_tiles, player):
        #if you can see it, it can see you
        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)

            elif player.fighter.hp > 0:
                monster.fighter.attack(player)