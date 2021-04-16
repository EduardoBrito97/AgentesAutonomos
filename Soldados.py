import random
from sc2.constants import *

class Soldados():
    def __init__(self, protoss_bot):
        self.bot = protoss_bot

    async def attack(self, unit_type):
         for soldado in self.bot.units(unit_type).ready:
                has_targets = self.bot.cached_known_enemy_units or self.bot.cached_known_enemy_structures
                if has_targets:
                    targets = (self.bot.cached_known_enemy_units | self.bot.cached_known_enemy_structures).filter(lambda unit: unit.can_be_attacked)
                    target = targets.closest_to(zealot)
                    await self.bot.do(soldado.attack(target))
                else:
                    await self.bot.do(soldado.attack(self.bot.enemy_start_locations[0]))

    async def do_work(self):
        bot = self.bot

        army_ready = (bot.units(STALKER).ready.amount >= 5 and bot.units(ZEALOT).ready.amount >= 5) or bot.units(ZEALOT).ready.amount > 10
        updates_ready = await bot.has_upgrade(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1) and await bot.has_upgrade(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1) and await bot.has_upgrade(FORGERESEARCH_PROTOSSSHIELDSLEVEL1)
        
        # Atacando
        if army_ready and updates_ready:
            await self.attack(ZEALOT)
            await self.attack(STALKER)