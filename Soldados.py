import random
from sc2.constants import *
from sc2.data import Alert

class Soldados():
    def __init__(self, protoss_bot):
        self.bot = protoss_bot

    async def attack(self, unit, target):
         await self.bot.do(unit.attack(target))
    
    async def move_and_attack(self, unit_type):
         for soldier in self.bot.units(unit_type).ready:
                has_targets = self.bot.cached_known_enemy_units or self.bot.cached_known_enemy_structures
                if has_targets:
                    targets = (self.bot.cached_known_enemy_units | self.bot.cached_known_enemy_structures).filter(lambda unit: unit.can_be_attacked)
                    target = targets.closest_to(soldier)
                    await self.attack(soldier, target)
                else:
                    await self.attack(soldier, self.bot.enemy_start_locations[0])
    
    async def defend(self, unit_type):
        for soldier in self.bot.units(unit_type).ready:
            nexus_amount = self.bot.units(NEXUS).amount

            # A gente dá prioridade a quem está atacando a base da gente
            if await self.are_we_under_attack(True):
                position_to_stand = self.bot.known_enemy_units.closest_to(self.bot.start_location).position
            else:
                closest_nexus = self.bot.units(NEXUS).closest_to(self.bot.enemy_start_locations[0])
                position_to_stand = closest_nexus.position.towards(self.bot.game_info.map_center, 8)
            
                if nexus_amount > 2:
                    position_to_stand = closest_nexus.position.towards(self.bot.start_location, 8)

            await self.attack(soldier, position_to_stand)

    async def are_we_under_attack(self, include_units):
        are_we_under_attack = self.bot.alert(Alert.BuildingUnderAttack) 
        if include_units:
            are_we_under_attack = are_we_under_attack or self.bot.alert(Alert.UnitUnderAttack)
        return are_we_under_attack

    async def attack_started(self):
        await self.bot.call_for_attack()

    # A Mothership voa, então precisamos que ela siga a tropa mais próxima, senão ela vai terminar atacando sozinha
    async def mothership_attack(self):
        if self.bot.units(MOTHERSHIP).ready:
            mothership = self.bot.units(MOTHERSHIP).ready.first
            soldier = (self.bot.units(ZEALOT).ready | self.bot.units(STALKER)).closest_to(mothership)
            if soldier:
                await self.attack(mothership, soldier.position)

    async def should_attack(self):
        bot = self.bot
        army_ready = (bot.units(STALKER).ready.amount >= 20 and bot.units(ZEALOT).ready.amount >= 20) or bot.units(ZEALOT).ready.amount > 40
        army_ready = army_ready and bot.units(MOTHERSHIP).ready.amount >= 1

        # Ter pelo menos todas as pequisas de lv 1 e a de dano de lv 2
        updates_ready = (await bot.has_upgrade(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2) 
                            and await bot.has_upgrade(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2)
                            and await bot.has_upgrade(FORGERESEARCH_PROTOSSSHIELDSLEVEL2))

        # Caso a gente tenha começado o ataque, ir até o fim (ou quse isso)
        focus_on_attack = bot.units(STALKER).ready.amount > 0 and bot.units(ZEALOT).ready.amount > 0 and self.bot.attack_in_course

        # Temos que dar prioridade a defesa caso nossa base esteja sob ataque
        return ((updates_ready and army_ready) or focus_on_attack) and await self.are_we_under_attack(False)

    async def do_work(self, iteration):
        # Atacando caso o batalhão esteja pronto, defendendo caso contrário
        if await self.should_attack() and iteration % 5 == 0:
            await self.move_and_attack(ZEALOT)
            await self.move_and_attack(STALKER)
            await self.mothership_attack()
            await self.attack_started()
        elif iteration % 10 == 0:
            await self.defend(ZEALOT)
            await self.defend(STALKER)
            await self.defend(MOTHERSHIP)
            await self.bot.retreat()
