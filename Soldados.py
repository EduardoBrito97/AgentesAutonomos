import random
from sc2.constants import *

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
            closest_nexus = self.bot.units(NEXUS).ready.closest_to(self.bot.enemy_start_locations[0])
            position_to_stand = closest_nexus.position.towards(self.bot.enemy_start_locations[0], 16)
            await self.attack(soldier, position_to_stand)

    async def do_work(self):
        bot = self.bot

        army_ready = (bot.units(STALKER).ready.amount >= 5 and bot.units(ZEALOT).ready.amount >= 5) or bot.units(ZEALOT).ready.amount > 10
        updates_ready = await bot.has_upgrade(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1) and await bot.has_upgrade(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1) and await bot.has_upgrade(FORGERESEARCH_PROTOSSSHIELDSLEVEL1)
        
        # Atacando caso o batalhão esteja pronto, defendendo caso contrário
        if army_ready and updates_ready:
            await self.move_and_attack(ZEALOT)
            await self.move_and_attack(STALKER)
        else:
            await self.defend(ZEALOT)
            await self.defend(STALKER)