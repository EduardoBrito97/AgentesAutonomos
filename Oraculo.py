import random
from sc2.constants import *

class Oraculo():
    def __init__(self, protoss_bot):
        self.bot = protoss_bot
        self.warpgate_started = False
        self.upgrades = []

    async def train_unit(self, unit, structure):
        for struct in self.bot.units(structure).ready:
                if self.bot.can_afford(unit) and struct.is_idle:
                   await self.bot.do(struct.train(unit))
    
    async def warp_unit(self, unit, structure):
        for struct in self.bot.units(structure).ready:
            if await self.bot.has_ability(WARPGATETRAIN_ZEALOT, struct) and self.bot.supply_left >= 2 and self.bot.can_afford(unit):
                pos = struct.position.to2.random_on_distance(4)
                placement = await self.bot.find_placement(WARPGATETRAIN_ZEALOT, pos, placement_step=2, )
                await self.bot.do(struct.warp_in(unit, placement))

    async def make_research(self, research, structure):
        if self.bot.units(structure).ready:
            struct = self.bot.units(structure).ready.first
            if self.bot.can_afford(research) and not research in self.upgrades and struct.is_idle:
                self.upgrades.append(research)
                await self.bot.do(struct(research))
                return True
        return False
        
    async def morph_gateways(self):
        for gateway in self.bot.units(GATEWAY):
            abilities = await self.bot.get_available_abilities(gateway)
            if MORPH_WARPGATE in abilities and self.bot.can_afford(MORPH_WARPGATE):
                await self.bot.do(gateway(MORPH_WARPGATE))

    async def do_work(self):
        bot = self.bot
        
        nexus = bot.units(NEXUS).ready.random

        # Se a gente não possui nenhum Nexus, ataque suicida
        if not self.bot.units(NEXUS).ready.exists:
            for worker in self.workers:
                await self.do(worker.attack(self.enemy_start_locations[0]))
            return

        # 16 Probes por Nexus
        if bot.workers.amount < bot.units(NEXUS).amount*16 and nexus.is_idle and bot.can_afford(PROBE):
            await bot.do(nexus.train(PROBE))
            return

        # Para criar os Stalkers
        if bot.units(CYBERNETICSCORE).ready.exists and bot.can_afford(RESEARCH_WARPGATE) and not self.warpgate_started:
            await self.make_research(RESEARCH_WARPGATE, CYBERNETICSCORE)
            self.warpgate_started = True
        
        # Atualizando Gateway em WarpGate
        if self.bot.units(GATEWAY).ready and not self.bot.units(WARPGATE) and not self.bot.already_pending(WARPGATE):
            await self.morph_gateways()

        # Fazendo os upgrades da Forge
        if await self.make_research(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1, FORGE):
            return
        
        if await self.make_research(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1, FORGE):
            return
        
        if await self.make_research(FORGERESEARCH_PROTOSSSHIELDSLEVEL1, FORGE):
            return

        # Criando a Mothership
        if bot.units(FLEETBEACON).ready.exists and bot.can_afford(MOTHERSHIP) and not bot.units(MOTHERSHIP) and not bot.already_pending(MOTHERSHIP):
            await bot.do(nexus.train(MOTHERSHIP))

        gateways_or_warp_gate_units_ready = bot.units(GATEWAY).ready.amount + bot.units(WARPGATE).ready.amount
        
        # Damos prioridade aos Stalkers que são mais fortes, mas custam mais
        if gateways_or_warp_gate_units_ready >= 2 and bot.units(STALKER).ready.amount <= 5 and self.warpgate_started:
            await self.train_unit(STALKER, GATEWAY)
            await self.warp_unit(STALKER, WARPGATE)

        # Já começamos a treinar Zealots, que são a base de nossa armada
        # Como Zealot usa só mineral, pode ser que tenhamos muito mineral e pouco gas
        should_create_zealot = bot.units(ZEALOT).ready.amount <= 5 or bot.minerals > 550
        if gateways_or_warp_gate_units_ready >= 2 and should_create_zealot:
            await self.train_unit(ZEALOT, GATEWAY)
            await self.warp_unit(ZEALOT, WARPGATE)