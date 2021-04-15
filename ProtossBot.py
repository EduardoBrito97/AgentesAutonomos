import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

class ProtossBot(sc2.BotAI):
    def __init__(self):
        self.warpgate_started = False

    async def on_step(self, iteration):
        await self.distribute_workers()
        
        if iteration == 0:
            await self.chat_send("GL HF")

        if not self.units(NEXUS).ready.exists:
            for worker in self.workers:
                await self.do(worker.attack(self.enemy_start_locations[0]))
            return

        # Foco em produzir assimilator perto de todos os nexus
        for nexus in self.units(NEXUS).ready:
            vgs = self.state.vespene_geyser.closer_than(20.0, nexus)
            for vg in vgs:
                if not self.can_afford(ASSIMILATOR):
                    break

                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break

                if not self.units(ASSIMILATOR).closer_than(1.0, vg).exists:
                    await self.do(worker.build(ASSIMILATOR, vg))

        nexus = self.units(NEXUS).ready.random

        # 16 probes por Nexus
        if self.workers.amount < self.units(NEXUS).amount*16 and nexus.is_idle and self.can_afford(PROBE):
            await self.do(nexus.train(PROBE))

        # Precisamos de ao menos 1 Pylon
        should_create_pylon = self.units(PYLON).amount == 0 or self.supply_left < 2
        # Mas também precisamos de Pylons sempre que não tivermos supplies
        should_create_pylon = should_create_pylon and not self.already_pending(PYLON) and self.can_afford(PYLON)
        
        if should_create_pylon:
            await self.build(PYLON, near = nexus)

        # Nosso foco é o Gateway, então precisamos construir pelo menos dois
        if self.units(GATEWAY).amount < 3 and self.units(PYLON).ready.amount > 0:
            pylon = self.units(PYLON).ready.random
            if pylon and self.can_afford(GATEWAY):
                await self.build(GATEWAY, near=pylon)
        
        # Em seguida, partimos para criar um Cybernetics Core
        if self.units(GATEWAY).ready.amount >= 2 and not self.units(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
            pylon = self.units(PYLON).ready.random
            if pylon and self.can_afford(CYBERNETICSCORE):
                await self.build(CYBERNETICSCORE, near = pylon)

        # Para criar os Stalkers
        elif self.units(CYBERNETICSCORE).ready.exists and self.can_afford(RESEARCH_WARPGATE) and not self.warpgate_started:
            ccore = self.units(CYBERNETICSCORE).ready.first
            await self.do(ccore(RESEARCH_WARPGATE))
            self.warpgate_started = True

        # Já começamos a treinar Zealots, que são a base de nossa armada
        if self.units(GATEWAY).ready.amount >= 2 and self.units(ZEALOT).ready.amount < 5:
            for gateway in self.units(GATEWAY).ready:
                if self.can_afford(ZEALOT) and gateway.is_idle:
                   await self.do(gateway.train(ZEALOT))

        # Por fim, criamos os Stalkers
        if self.units(GATEWAY).ready.amount >= 2 and self.units(STALKER).ready.amount < 5:
            for gateway in self.units(GATEWAY).ready:
                if self.can_afford(STALKER) and gateway.is_idle:
                   await self.do(gateway.train(STALKER))

        army_is_ready = self.units(STALKER).ready.amount > 5 and self.units(ZEALOT).ready.amount > 5
        
        # Atacando
        if army_is_ready:
            for vr in self.units(ZEALOT).ready.idle:
                await self.do(vr.attack(self.enemy_start_locations[0]))
            
            for vr in self.units(STALKER).ready.idle:
                await self.do(vr.attack(self.enemy_start_locations[0]))


def main():
    sc2.run_game(
        sc2.maps.get("AcropolisLE"),
        [Bot(Race.Protoss, ProtossBot(), name="Botzada"), Computer(Race.Protoss, Difficulty.Medium)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
