import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random
from sc2.constants import *

class Soldados():
    def __init__(self, protoss_bot):
        self.bot = protoss_bot
        self.start_location_cleaned = False
        self.attack_targets_index = 0
        
        # Temos uma lista de alvos para quando formos atacar
        self.attack_targets = []

        # Começamos pelo local de início do inimigo
        self.attack_targets.append(protoss_bot.enemy_start_locations[0])
        
        # Depois vamos atrás de todas as expansões possíveis no jogo, em ordem de distância do inimigo
        expansions = protoss_bot.expansion_locations_list
        expansions = sorted(expansions, key = lambda x: x.distance_to(protoss_bot.enemy_start_locations[0]))
        for expansion in expansions:
            self.attack_targets.append(expansion)
        
        # Por fim, voltamos ao nosso lugar (se não tivermos ganho ou perdido até aqui o jogo tá bugado, pq significa que o inimigo não tá em canto nenhum)
        self.attack_targets.append(protoss_bot.start_location)

    async def attack(self, unit, target):
        unit.attack(target)
    
    async def move_and_attack(self, unit_type):
        has_targets = (self.bot.enemy_units | self.bot.enemy_structures)
        num_of_soldiers_without_targets = 0
        for soldier in self.bot.units(unit_type).ready:
            if has_targets:
                targets = (self.bot.enemy_units | self.bot.enemy_structures).filter(lambda unit: unit.can_be_attacked)
                if targets:
                    await self.attack(soldier, targets.closest_to(soldier))
            else:
                distance_to_enemy_start = self.attack_targets[self.attack_targets_index].distance_to(soldier)
                if distance_to_enemy_start > 3:
                    await self.attack(soldier, self.attack_targets[self.attack_targets_index])
                else:
                    num_of_soldiers_without_targets += 1
                
        if self.attack_targets_index < len(self.attack_targets) - 1 and num_of_soldiers_without_targets > 10:
                self.attack_targets_index += 1
    
    async def defend(self, unit_type):
        nexus_amount = self.bot.townhalls.amount
        enemy_units = self.bot.enemy_units.filter(lambda unit: unit.can_be_attacked)
        nexus_closest_to_enemy = self.bot.townhalls.closest_to(self.bot.enemy_start_locations[0])

        for soldier in self.bot.units(unit_type).ready:
            # A gente dá prioridade a quem está atacando a base da gente
            if await self.are_we_under_attack():
                closest_enemy = enemy_units.closest_to(nexus_closest_to_enemy)
                await self.attack(soldier, closest_enemy)
            else:
                position_to_stand = nexus_closest_to_enemy.position.towards(self.bot.game_info.map_center, 8)
                if nexus_amount > 2:
                    position_to_stand = nexus_closest_to_enemy.position.towards(self.bot.start_location, 8)

                await self.attack(soldier, position_to_stand)

    async def are_we_under_attack(self):
        for nexus in self.bot.townhalls:
            nearby_enemies = self.bot.enemy_units.closer_than(30, nexus)
            if nearby_enemies.amount >= 2:
                return True
        return False

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
        sum_of_troops = bot.units(STALKER).ready.amount + bot.units(ZEALOT).ready.amount

        army_ready = sum_of_troops > 30
        army_ready = army_ready and bot.units(MOTHERSHIP).ready.amount >= 1

        # Ter pelo menos todas as pequisas de lv 1 e a de dano de lv 2
        updates_ready = (await bot.has_upgrade(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2) 
                            and await bot.has_upgrade(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2)
                            and await bot.has_upgrade(FORGERESEARCH_PROTOSSSHIELDSLEVEL2))

        # Caso a gente tenha começado o ataque, ir até o fim (ou quse isso)
        focus_on_attack = sum_of_troops > 0 and self.bot.attack_in_course

        # Temos que dar prioridade a defesa caso nossa base esteja sob ataque
        return ((updates_ready and army_ready) or focus_on_attack) and not await self.are_we_under_attack()

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
