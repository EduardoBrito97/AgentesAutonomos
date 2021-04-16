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

    async def make_research(self, research, structure):
        if self.bot.units(structure).ready:
            struct = self.bot.units(structure).ready.first
            if self.bot.can_afford(research) and not research in self.upgrades and struct.is_idle:
                self.upgrades.append(research)
                await self.bot.do(struct(research))
                return True
        return False
        

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
        # if bot.units(GATEWAY).ready and not bot.units(WARPGATE) and not bot.already_pending(WARPGATE):
        #     gateway = bot.units(GATEWAY).ready.first
        #     abilities = await bot.get_available_abilities(gateway)
        #     if MORPH_WARPGATE in abilities and bot.can_afford(MORPH_WARPGATE):
        #         await bot.do(gateway(MORPH_WARPGATE))

        # Fazendo os upgrades da Forge
        if await self.make_research(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1, FORGE):
            return
        
        if await self.make_research(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1, FORGE):
            return
        
        if await self.make_research(FORGERESEARCH_PROTOSSSHIELDSLEVEL1, FORGE):
            return

        # Criando a Mothership
        if self.units(FLEETBEACON).ready.exists and self.can_afford(MOTHERSHIPCORE) and not self.units(MOTHERSHIPCORE):
            await self.do(nexus.train(MOTHERSHIPCORE))

        gateways_or_warp_gate_units_ready = bot.units(GATEWAY).ready.amount + bot.units(WARPGATE).ready.amount
        
        # Damos prioridade aos Stalkers que são mais fortes, mas custam mais
        if gateways_or_warp_gate_units_ready >= 2 and bot.units(STALKER).ready.amount <= 5 and self.warpgate_started:
            await self.train_unit(STALKER, GATEWAY)
            # await self.train_unit(STALKER, WARPGATE)

        # Já começamos a treinar Zealots, que são a base de nossa armada
        # Como Zealot usa só mineral, pode ser que tenhamos muito mineral e pouco gas
        should_create_zealot = bot.units(ZEALOT).ready.amount <= 5 or bot.minerals > 800
        if gateways_or_warp_gate_units_ready >= 2 and should_create_zealot:
            await self.train_unit(ZEALOT, GATEWAY)
            #await self.train_unit(ZEALOT, WARPGATE)