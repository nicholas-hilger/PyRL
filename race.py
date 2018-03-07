class Race:
    def __init__(self, name="", hp=0, att=0, wis=0, defense=0):
        self.name = name
        self.hp = hp
        self.att = att
        self.wis = wis
        self.defense = defense


class Human(Race):
    def __init__(self):
        super().__init__(name="Human", hp=150, att=2, wis=2)


class Golem(Race):
    def __init__(self):
        super().__init__(name="Golem", hp=175, att=2, wis=1, defense=1)


class Denizen(Race):
    def __init__(self):
        super().__init__(name="Denizen", hp=125, att=3, wis=2, defense=0)


class Demon(Race):
    def __init__(self):
        super().__init__(name="Demon", hp=100, att=4, wis=2, defense=0)