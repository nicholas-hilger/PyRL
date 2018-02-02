import colors
import math
from death_functions import *
from config import *
import random


class BasicMonster:
    # AI for a basic monster
    def take_turn(self, visible_tiles, player, turns, message, my_map, objects):
        # if you can see it, it can see you
        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y, my_map, objects)

            elif player.hp > 0 and turns % monster.spd == 0:
                monster.attack(player, message, player, objects)


class ConfusedMonster:
    def __init__(self, old_ai, message, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns
        self.message = message

    def take_turn(self, visible_tiles, player, turns, message, my_map, objects):
        if self.num_turns > 0:
            self.owner.move(random.randint(-1, 1), random.randint(-1, 1), my_map, objects)

            self.num_turns -= 1

        else:
            self.owner.ai = self.old_ai
            self.message('The ' + self.owner.name + ' is no longer confused!', colors.red)

class GameObject:
    # A generic object. Always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False, creature=0, item=0):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.creature = creature
        self.item = item

    def is_blocked(x, y, my_map, objects):
        if my_map[x][y].blocked:
            return True

        for obj in objects:
            if obj.blocks and obj.x == x and obj.y == y:
                return True

        return False

    def move(self, dx, dy, my_map, objects):
        if not GameObject.is_blocked(self.x + dx, self.y + dy, my_map, objects):
            self.x += dx
            self.y += dy

    def move_or_attack(self, dx, dy, objects, message, my_map, player):
        x = self.x + dx
        y = self.y + dy

        target = None
        for obj in objects:
            if obj.x == x and obj.y == y and obj.blocks:
                target = obj
                break
        if target is not None and target.ai:
            self.attack(target, message, player, objects)
        else:
            self.move(dx, dy, my_map, objects)

    def draw(self, con, vis_tiles):
        if (self.x, self.y) in vis_tiles:
            con.draw_char(self.x, self.y, self.char, self.color, bg=None)

    def clear(self, con):
        con.draw_char(self.x, self.y, ' ', self.color, bg=None)

    def move_towards(self, target_x, target_y, my_map, objects):
        # vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # normalize it to length 1 (preserving direction) then round it and
        # convert to int so the movement is restricted to the grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy, my_map, objects)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def send_to_back(self, objects):
        objects.remove(self)
        objects.insert(0, self)


class Fighter(GameObject):
    # Combat-related properties and methods

    def __init__(self, x, y, char, name, color, hp, blocks=False, ai=None, defense=0, cut=0, blunt=0, pierce=0, magic=0,
                 cut_weak=1, blunt_weak=1, pierce_weak=1, magic_weak=1, att=0, wis=0, xp=0, gold=0, spd=1,
                 death_function=None, lvl=1, creature=1, wep=None, helm=None, chest=None, pants=None, shield=None):

        super().__init__(x=x, y=y, char=char, name=name, color=color, blocks=blocks, creature=creature)

        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.cut = cut
        self.blunt = blunt
        self.pierce = pierce
        self.magic = magic
        self.cut_weak = cut_weak
        self.blunt_weak = blunt_weak
        self.pierce_weak = pierce_weak
        self.magic_weak = magic_weak
        self.xp = 0
        self.max_xp = xp
        self.death_function = death_function
        self.lvl = lvl
        self.wis = wis
        self.att = att
        self.gold = gold
        self.spd = spd
        self.creature = creature
        self.wep = wep
        self.helm = helm
        self.chest = chest
        self.pants = pants
        self.shield = shield

        if ai is not None:
            self.ai = ai()
            self.ai.owner = self
        else:
            self.ai = None

    def take_damage(self, damage, message, player, objects):
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            func = self.death_function
            if func is not None:
                if self != player:
                    func(self, message, player, objects)
                else:
                    func(self, message)

    def attack(self, target, message, player, objects):
            damage = 0
            if self.blunt > 0:
                damage += int((self.att + self.blunt) * target.blunt_weak)
            if self.cut > 0:
                damage += int((self.att + self.cut) * target.cut_weak)
            if self.pierce > 0:
                damage += int((self.att + self.pierce) * target.pierce_weak)
            if self.magic > 0:
                damage += int((self.wis + self.magic) * target.magic_weak)

            damage -= target.defense

            damage_type = max(self.blunt, self.cut, self.pierce, self.magic)

            damage_adj = ' attacks '

            if damage_type == self.blunt:
                damage_adj = ' smashes '
            elif damage_type == self.pierce:
                damage_adj = ' stabs '
            elif damage_type == self.cut:
                damage_adj = ' slashes '
            elif damage_type == self.magic:
                damage_adj = ' blasts '

            if damage > 0:
                message(self.name + damage_adj + target.name + ' for ' + str(damage) + ' damage.')
                target.take_damage(damage, message, player, objects)
            else:
                message(self.name + ' tries to attack ' + target.name + ', but whiffs!')

    def check_xp(self, player, message):
        if self.xp >= self.max_xp:
            self.xp -= self.max_xp
            self.max_xp = int(float(self.max_xp * 1.3))
            self.max_hp += 15
            self.hp += 10
            self.att += 1
            self.wis += 1
            self.lvl += 1
            message(player.name + ' is now level ' + str(player.lvl) + '!', colors.dark_green)

    def check_limits(self):
        if self.hp > self.max_hp:
            self.hp = self.max_hp

        if self.gold > 9999:
            self.gold = 9999

        if self.att < 1:
            self.att = 1
        if self.att > 99:
            self.att = 99

        if self.defense < 1:
            self.defense = 1
        if self.defense > 99:
            self.defense = 99

        if self.wis < 1:
            self.wis = 1
        if self.wis > 99:
            self.wis = 99

    def heal(self, amount):
        self.hp += amount
        self.check_limits()


class Goblin(Fighter):
    def __init__(self, x, y):
        super().__init__(x, y, char='g', name='Goblin', color=colors.darker_green, hp=27, blocks=True, ai=BasicMonster, defense=1,
                         cut=7, magic_weak=1.5, cut_weak=1.5, xp=8, gold=15, spd=3, death_function=monster_death, lvl=1, creature=1)


class Slug(Fighter):
    def __init__(self, x, y):
        super().__init__(x, y, char='s', name='Slug', color=colors.amber, hp=19, blocks=True, ai=BasicMonster, defense=1,
                         blunt=4, pierce_weak=1.5, xp=5, gold=28, spd=2, death_function=monster_death, lvl=1, creature=1)


class LesserUndead(Fighter):
    def __init__(self, x, y):
        super().__init__(x, y, char='u', name='Lesser Undead', color=colors.gray, hp=15, blocks=True, ai=BasicMonster, defense=0,
                         pierce=5, pierce_weak=0.5, cut_weak=0.5, blunt_weak=2, xp=7, gold=20, spd=1, death_function=monster_death, lvl=1, creature=1)


class Item(GameObject):
    def __init__(self, x, y, char, name, color, blocks=False, ai=None, hp=0, att=0, wis=0, fighter=None, item=1, use_function=None):

        super().__init__(x=x, y=y, char=char, name=name, color=color, blocks=blocks, item=1)

        self.hp = hp
        self.att = att
        self.wis = wis
        self.fighter = fighter
        self.item = item
        self.use_function = use_function

        if ai is not None:
            self.ai = ai()
            self.ai.owner = self
        else:
            self.ai = None

    def pick_up(self, inventory, message, objects):
        if len(inventory) >= 26:
            message('Your inventory is full! You leave ' + self.name + ' behind.', colors.light_red)
        else:
            inventory.append(self)
            objects.remove(self)
            message('You pick up the ' + self.name + '.', colors.green)

    def use(self, inventory, message):
        if self.use_function is None:
            message('The ' + self.name + ' cannot be used.', colors.light_red)
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self) #destroy after use, unless it was cancelled for some reason

    def equip(self, player, message, inventory):
        if self.use_function is None:
            if self.type == 'weapon':
                if player.wep is not None:
                    temp_wep = player.wep
                    player.wep = self
                    inventory.append(temp_wep)

                if len(inventory) > 0:
                    inventory.remove(self)
                player.wep = self
                player.cut = self.cut
                player.pierce = self.pierce
                player.blunt = self.blunt
                player.magic = self.magic

            message(player.name + ' equips the ' + self.name + '.', colors.magenta)

        else:
            message(self.name + ' can\'t be equipped.', colors.red)


class LesserHealingPotion(Item):
    def __init__(self, x, y, use_function=None):
        super().__init__(x=x, y=y, char='!', name='Lesser Healing Potion', color=colors.lighter_violet, ai=None, blocks=False, use_function=use_function)


class HealingPotion(Item):
    def __init__(self, x, y, use_function=None):
        super().__init__(x=x, y=y, char='!', name='Healing Potion', color=colors.violet, ai=None, blocks=False, use_function=use_function)


class LightningScroll(Item):
    def __init__(self, x, y, use_function=None):
        super().__init__(x=x, y=y, char='?', name='Scroll of Lightning Bolt', color=SCROLL_COLOR, ai=None, blocks=False, use_function=use_function)


class ConfuseScroll(Item):
    def __init__(self, x, y, use_function=None):
        super().__init__(x=x, y=y, char='?', name='Scroll of Confusion', color=SCROLL_COLOR, ai=None, blocks=False, use_function=use_function)


class FireballScroll(Item):
    def __init__(self, x, y, use_function=None):
        super().__init__(x=x, y=y, char='?', name='Scroll of Fireball', color=SCROLL_COLOR, ai=None, blocks=False, use_function=use_function)


class Equipment(Item):
    def __init__(self, x, y, char, name, color, blocks=False, ai=None, fighter=None, item=1, cut=0, blunt=0, pierce=0, magic=0, ranged=0, use_function=None, type=None):

        super().__init__(x=x, y=y, char=char, name=name, color=color, blocks=False, ai=None, fighter=None, item=1, use_function=use_function)

        self.cut = cut
        self.pierce = pierce
        self.blunt = blunt
        self.magic = magic
        self.ranged = ranged
        self.use_function = use_function
        self.type = type

        if ai is not None:
            self.ai = ai()
            self.ai.owner = self
        else:
            self.ai = None


class RustySword(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Rusty Sword', color=colors.silver, fighter=None, ai=None, blocks=False, use_function=None, cut=6, type='weapon')


class ChippedMace(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Chipped Mace', color=colors.silver, fighter=None, ai=None, blocks=False, use_function=None, blunt=5, type='weapon')


class BentSpear(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Bent Spear', color=colors.silver, fighter=None, ai=None, blocks=False, use_function=None, pierce=8, type='weapon')


class OldWhip(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Old Whip', color=colors.silver, fighter=None, ai=None, blocks=False, use_function=None, cut=5, magic=2, type='weapon')