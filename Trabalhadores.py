import random
from sc2.constants import *

class Trabalhadores():
    def __init__(self, protoss_bot):
        self.bot = protoss_bot

    async def build_gas_assimilators(self):
        for nexus in self.bot.units(NEXUS).ready:
            vgs = self.bot.state.vespene_geyser.closer_than(20.0, nexus)
            for vg in vgs:
                if not self.bot.can_afford(ASSIMILATOR):
                    break

                worker = self.bot.select_build_worker(vg.position)
                if worker is None:
                    break

                if not self.bot.units(ASSIMILATOR).closer_than(1.0, vg).exists:
                    await self.bot.do(worker.build(ASSIMILATOR, vg))
    
    async def build_pylons(self):
        bot = self.bot
        nexus = bot.units(NEXUS).ready.random
        int_rand = random.randint(0, 8)

        amount_of_structures = bot.units(GATEWAY).amount + bot.units(CYBERNETICSCORE).amount + bot.units(FLEETBEACON).amount + bot.units(STARGATE).amount
       
        # Precisamos de ao menos 1 Pylon, mas também precisamos de Pylons sempre que não tivermos supplies
        should_create_pylon = bot.units(PYLON).amount == 0 or bot.supply_left < 2

        # Precisamos de 1 Pylon pra cada estrutura tbm
        should_create_pylon = should_create_pylon or bot.units(PYLON).amount <= amount_of_structures

        # Por fim, analisamos se é possível construir um Pylon (ou se já temos algum em construção)
        should_create_pylon = should_create_pylon and not bot.already_pending(PYLON) and bot.can_afford(PYLON)

        if should_create_pylon:
            await bot.build(PYLON, near = nexus.position.towards(bot.game_info.map_center, int_rand))

    async def build_structure(self, structure):
        int_rand = random.randint(0, 8)

        if not self.bot.already_pending(structure):
            pylon = self.bot.units(PYLON).ready.random
            if pylon and self.bot.can_afford(structure):
                await self.bot.build(structure, near = pylon.position.towards(self.bot.game_info.map_center, int_rand))

    async def do_work(self, iteration):
        bot = self.bot

        if iteration % 10 == 0:
            await self.bot.distribute_workers()

        # Foco em produzir assimilator perto de todos os nexus
        await self.build_gas_assimilators()
        
        # Precisamos de Pylons
        await self.build_pylons()
        
        gateways_or_warp_gate_units = bot.units(GATEWAY).amount + bot.units(WARPGATE).amount 
        # Nosso foco é o Gateway, então precisamos construir pelo menos dois
        if gateways_or_warp_gate_units < 3 and bot.units(PYLON).ready.amount > 0 :
            await self.build_structure(GATEWAY)
            return

        gateways_or_warp_gate_units_ready = bot.units(GATEWAY).ready.amount + bot.units(WARPGATE).ready.amount 
        # Em seguida, partimos para criar um Cybernetics Core
        if gateways_or_warp_gate_units_ready >= 2 and not bot.units(CYBERNETICSCORE):
            await self.build_structure(CYBERNETICSCORE)
            return
        
        # Em seguida, criamos a Forge pra fazer os upgrades
        if gateways_or_warp_gate_units_ready >= 2 and not bot.units(FORGE):
            await self.build_structure(FORGE)
            return

        # Criando a Stargate para a Mothership Core
        if bot.units(CYBERNETICSCORE).ready.exists and not bot.units(STARGATE):
            await self.build_structure(STARGATE)
            return

        # Criando a Fleet Beacon para a Mothership Core
        if bot.units(STARGATE).ready.exists and not bot.units(FLEETBEACON):
            await self.build_structure(FLEETBEACON)

        