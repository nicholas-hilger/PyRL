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


class BasicRangedMonster:
    # AI for a basic monster
    def take_turn(self, visible_tiles, player, turns, message, my_map, objects):
        # if you can see it, it can see you
        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:
            if monster.distance_to(player) >= 6:
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
            blocked = 0
            confuse_hit = 0

            if self.blunt > 0:
                damage += int((self.att + self.blunt) * target.blunt_weak)
                confuse_chance = random.randint(0, 100)
                if confuse_chance < (15 + int(self.blunt/10)) and target != player:
                    confuse_hit = 1
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

            if target == player:
                if target.shield is not None:
                    block_chance = random.randint(0, 100)
                    if block_chance < target.shield.block:
                        blocked = 1

            if damage > 0 and not blocked:
                message(self.name + damage_adj + target.name + ' for ' + str(damage) + ' damage.')
                if confuse_hit:
                    message(target.name + ' got hit so hard, they\'re now confused!', colors.gray)
                    target.old_ai = target.ai
                    target.ai = ConfusedMonster(target.old_ai, message)
                    target.ai.owner = target

                target.take_damage(damage, message, player, objects)
            else:
                if not blocked:
                    message(self.name + ' tries to attack ' + target.name + ', but whiffs!')
                else:
                    message(self.name + ' tries to attack ' + target.name + ', but is blocked!')

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

        if self.defense < 0:
            self.defense = 0
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
                         cut=5, magic_weak=1.5, cut_weak=1.5, xp=8, gold=15, spd=3, death_function=monster_death, lvl=1, creature=1)


class Slug(Fighter):
    def __init__(self, x, y):
        super().__init__(x, y, char='s', name='Slug', color=colors.amber, hp=19, blocks=True, ai=BasicMonster, defense=1,
                         blunt=4, pierce_weak=1.5, xp=5, gold=28, spd=2, death_function=monster_death, lvl=1, creature=1)


class LesserGhoul(Fighter):
    def __init__(self, x, y):
        super().__init__(x, y, char='u', name='Lesser Ghoul', color=colors.gray, hp=15, blocks=True, ai=BasicMonster, defense=0,
                         pierce=4, pierce_weak=0.5, cut_weak=0.5, blunt_weak=2, xp=7, gold=20, spd=1, death_function=monster_death, lvl=1, creature=1)


class Imp(Fighter):
    def __init__(self, x, y):
        super().__init__(x, y, char='i', name='Imp', color=colors.lighter_red, hp=7, blocks=True, ai=BasicRangedMonster, defense=0,
                         magic=2, pierce=1, magic_weak=0, blunt_weak=2, pierce_weak=2, cut_weak=2,  xp=9, gold=20, spd=2, death_function=monster_death, lvl=1, creature=1)


class Item(GameObject):
    def __init__(self, x, y, char, name, color, blocks=False, ai=None, hp=0, att=0, wis=0, fighter=None, item=1, use_function=None, type=''):

        super().__init__(x=x, y=y, char=char, name=name, color=color, blocks=blocks, item=1)

        self.hp = hp
        self.att = att
        self.wis = wis
        self.fighter = fighter
        self.item = item
        self.use_function = use_function
        self.type = type

        if ai is not None:
            self.ai = ai()
            self.ai.owner = self
        else:
            self.ai = None

    def pick_up(self, inventory, message, objects, player):
        if len(inventory) >= 26:
            message('Your inventory is full! You leave ' + self.name + ' behind.', colors.light_red)
        else:
            if self.name != 'Gold':
                inventory.append(self)
                objects.remove(self)
                message('You pick up the ' + self.name + '.', colors.green)
            else:
                gain = random.randint(1, 25)
                player.gold += gain
                message('You pick up ' + str(gain) + ' gold.', colors.yellow)
                objects.remove(self)

    def use(self, inv, message):
        if self.use_function is None:
            message('The ' + self.name + ' cannot be used.', colors.light_red)
        else:
            if self.use_function() != 'cancelled':
                inv.remove(self) #destroy after use, unless it was cancelled for some reason

    def drop(self, inventory, objects, message, player):
        objects.append(self)
        inventory.remove(self)
        self.x = player.x
        self.y = player.y
        message('You drop the ' + self.name + ".", colors.lighter_red)

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

            elif self.type == 'chest':
                if player.chest is not None:
                    temp_chest = player.chest
                    player.defense -= temp_chest.defense
                    player.chest = self
                    inventory.append(temp_chest)

                if len(inventory) > 0:
                    inventory.remove(self)
                player.chest = self
                player.cut_weak = self.cut_weak
                player.blunt_weak = self.blunt_weak
                player.pierce_weak = self.pierce_weak
                player.magic_weak = self.magic_weak
                player.defense += self.defense
                player.color = self.color

            elif self.type == 'pants':
                if player.pants is not None:
                    temp_pants = player.pants
                    player.pants = self
                    inventory.append(temp_pants)
                    player.defense -= temp_pants.defense

                if len(inventory) > 0:
                    inventory.remove(self)
                player.pants = self
                player.defense += self.defense

            elif self.type == 'helm':
                if player.helm is not None:
                    temp_helm = player.helm
                    player.helm = self
                    inventory.append(temp_helm)
                    player.defense -= temp_helm.defense

                if len(inventory) > 0:
                    inventory.remove(self)
                player.helm = self
                player.defense += self.defense

            elif self.type == 'shield':
                if player.shield is not None:
                    temp_shield = player.shield
                    player.shield = self
                    inventory.append(temp_shield)

                if len(inventory) > 0:
                    inventory.remove(self)
                player.shield = self

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


class Gold(Item):
    def __init__(self, x, y, use_function=None):
        super().__init__(x=x, y=y, char='$', name='Gold', color=colors.yellow, ai=None, blocks=False, use_function=use_function)


class Equipment(Item):
    def __init__(self, x, y, char, name, color, blocks=False, ai=None, fighter=None, item=1, cut=0, blunt=0, pierce=0, magic=0, ranged=0,
                 defense=0, cut_weak=1, blunt_weak=1, magic_weak=1, pierce_weak=1, use_function=None, type=None, block=0):

        super().__init__(x=x, y=y, char=char, name=name, color=color, blocks=False, ai=None, fighter=None, item=1, use_function=use_function)

        self.cut = cut
        self.pierce = pierce
        self.blunt = blunt
        self.magic = magic
        self.ranged = ranged
        self.defense = defense
        self.cut_weak = cut_weak
        self.blunt_weak = blunt_weak
        self.pierce_weak = pierce_weak
        self.magic_weak = magic_weak
        self.defense = defense
        self.block = block

        self.use_function = use_function
        self.type = type

        if ai is not None:
            self.ai = ai()
            self.ai.owner = self
        else:
            self.ai = None


class RustySword(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Rusty Sword', color=colors.orange, fighter=None, ai=None, blocks=False, use_function=None, cut=8, type='weapon')


class ChippedMace(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Chipped Mace', color=colors.silver, fighter=None, ai=None, blocks=False, use_function=None, blunt=7, type='weapon')


class BentSpear(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Bent Spear', color=colors.sepia, fighter=None, ai=None, blocks=False, use_function=None, pierce=8, type='weapon')


class OldWhip(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Old Whip', color=colors.dark_sepia, fighter=None, ai=None, blocks=False, use_function=None, cut=5, magic=2, type='weapon')


class CrackedAxe(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Cracked Axe', color=colors.red, fighter=None, ai=None, blocks=False, use_function=None, cut=5, blunt=3, type='weapon')


class Mournblade(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Mournblade', color=colors.purple, fighter=None, ai=None, blocks=False, use_function=None, cut=14, magic=8, type='weapon')


class Trident(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Trident', color=colors.dark_yellow, fighter=None, ai=None, blocks=False, use_function=None, pierce=12, magic=3, type='weapon')


class ChainWhip(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='/', name='Chain Whip', color=colors.gray, fighter=None, ai=None, blocks=False, use_function=None, cut=9, blunt=7, type='weapon')


class RedMail(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='[', name='Red Mail', color=colors.dark_crimson, fighter=None, ai=None, blocks=False, use_function=None, cut_weak=0.5, blunt_weak=0.5, magic_weak=0.5, pierce_weak=0.5, defense=1, type='chest')


class Coat(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='[', name='Coat', color=colors.sepia, fighter=None, ai=None, blocks=False, use_function=None, cut_weak=0.75, type='chest')


class LeatherVest(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='[', name='Leather Vest', color=colors.sepia, fighter=None, ai=None, blocks=False, use_function=None, cut_weak=0.5, defense=1, type='chest')


class Trousers(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='[', name='Trousers', color=colors.lighter_sepia, fighter=None, ai=None, blocks=False, use_function=None, defense=1, type='pants')


class PlatedJeans(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='[', name='Plated Jeans', color=colors.light_blue, fighter=None, ai=None, blocks=False, use_function=None, defense=2, type='pants')


class Hat(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='[', name='Hat', color=colors.dark_sepia, fighter=None, ai=None, blocks=False, use_function=None, defense=1, type='helm')


class Bucket(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char='[', name='Bucket', color=colors.dark_gray, fighter=None, ai=None, blocks=False, use_function=None, defense=2, type='helm')


class PlankShield(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char=']', name='Plank Shield', color=colors.light_sepia, fighter=None, ai=None, blocks=False, use_function=None, block=5, type='shield')


class PotLid(Equipment):
    def __init__(self, x, y):
        super().__init__(x=x, y=y, char=']', name='Pot Lid', color=colors.gray, fighter=None, ai=None, blocks=False, use_function=None, block=10, type='shield')