import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random
from sc2.constants import *

class Oraculo():
    def __init__(self, protoss_bot):
        self.bot = protoss_bot
        self.warpgate_started = False
        self.upgrades = []

    async def train_unit(self, unit, structure):
        for struct in self.bot.structures(structure).ready:
                if self.bot.can_afford(unit) and struct.is_idle: 
                   struct.train(unit)
    
    async def warp_unit(self, unit, structure):
        for struct in self.bot.structures(structure).ready:
            if await self.bot.has_ability(WARPGATETRAIN_ZEALOT, struct) and self.bot.supply_left >= 2 and self.bot.can_afford(unit):
                closest_to_unit = self.bot.townhalls.closest_to(self.bot.enemy_start_locations[0])
                if self.bot.attack_in_course:
                    closest_to_unit = self.bot.enemy_start_locations[0]

                pos = self.bot.structures(PYLON).closest_to(closest_to_unit).position.to2.random_on_distance(4)
                placement = await self.bot.find_placement(WARPGATETRAIN_ZEALOT, pos, placement_step=2)
                if placement != None:
                    struct.warp_in(unit, placement)

    async def make_research(self, research, structure):
        for struct in self.bot.structures(structure).ready:
            if not self.bot.can_afford(research) or research in self.upgrades:
                break 
            elif self.bot.can_afford(research) and not research in self.upgrades and struct.is_idle:
                self.upgrades.append(research)
                struct(research)
                return True
        return False
        
    async def morph_gateways(self):
        for gateway in self.bot.structures(GATEWAY):
            abilities = await self.bot.get_available_abilities(gateway)
            if MORPH_WARPGATE in abilities and self.bot.can_afford(MORPH_WARPGATE):
                gateway(MORPH_WARPGATE)

    async def do_work(self):
        bot = self.bot
        
        nexus = bot.townhalls.ready.random

        # Se a gente n??o possui nenhum Nexus, ataque suicida
        if not self.bot.townhalls.ready.exists:
            for worker in self.workers:
                await worker.attack(self.enemy_start_locations[0])
            return

        # 16 Probes por Nexus, no m??ximo 40
        if bot.workers.amount < bot.townhalls.amount*16 and bot.workers.amount < 36 and nexus.is_idle and bot.can_afford(PROBE) and not self.bot.save_mineral:
            nexus.train(PROBE)
            return

        # Para criar os Stalkers
        if bot.structures(CYBERNETICSCORE).ready.exists and bot.can_afford(RESEARCH_WARPGATE) and not self.warpgate_started:
            await self.make_research(RESEARCH_WARPGATE, CYBERNETICSCORE)
            self.warpgate_started = True
        
        # Atualizando Gateway em WarpGate
        if self.bot.structures(GATEWAY).ready and not self.bot.structures(WARPGATE) and not self.bot.already_pending(WARPGATE):
            await self.morph_gateways()

        # Fazendo os upgrades da Forge
        if not self.bot.save_gas and await self.make_research(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1, FORGE):
            return
        
        if not self.bot.save_gas and await self.make_research(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1, FORGE):
            return
        
        if not self.bot.save_gas and await self.make_research(FORGERESEARCH_PROTOSSSHIELDSLEVEL1, FORGE):
            return

        # Fazendo os upgrades lv 2 da Forge
        if not self.bot.save_gas and self.bot.structures(TWILIGHTCOUNCIL).ready and await self.make_research(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2, FORGE):
            return
        
        if not self.bot.save_gas and self.bot.structures(TWILIGHTCOUNCIL).ready and await self.make_research(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2, FORGE):
            return
        
        if not self.bot.save_gas and self.bot.structures(TWILIGHTCOUNCIL).ready and await self.make_research(FORGERESEARCH_PROTOSSSHIELDSLEVEL2, FORGE):
            return

        # Guardando recursos de gas para a Mothership
        if bot.structures(FLEETBEACON).ready.exists and not bot.units(MOTHERSHIP) and not bot.already_pending(MOTHERSHIP):
            await self.bot.set_save_gas(True)

        # Criando a Mothership
        if bot.structures(FLEETBEACON).ready.exists and bot.can_afford(MOTHERSHIP) and not bot.units(MOTHERSHIP) and not bot.already_pending(MOTHERSHIP) and not self.bot.save_mineral:
            nexus.train(MOTHERSHIP)
            await self.bot.set_save_gas(False)
            return

        gateways_or_warp_gate_units_ready = bot.structures(GATEWAY).ready.amount + bot.structures(WARPGATE).ready.amount
        
        # Damos prioridade aos Stalkers que s??o mais fortes, mas custam mais, por??m, caso pudermos construir a Mothership, dar prioridade a ela
        if gateways_or_warp_gate_units_ready >= 2 and bot.units(STALKER).ready.amount <= 40 and self.bot.can_afford(STALKER) and self.warpgate_started and not self.bot.save_gas and not self.bot.save_mineral:
            await self.train_unit(STALKER, GATEWAY)
            await self.warp_unit(STALKER, WARPGATE)
            return

        # J?? come??amos a treinar Zealots, que s??o a base de nossa armada
        # Como Zealot usa s?? mineral, pode ser que tenhamos muito mineral e pouco gas
        should_create_zealot = bot.units(ZEALOT).ready.amount <= 40 or bot.minerals > 550
        if gateways_or_warp_gate_units_ready >= 2 and should_create_zealot and not self.bot.save_mineral:
            await self.train_unit(ZEALOT, GATEWAY)
            await self.warp_unit(ZEALOT, WARPGATE)
