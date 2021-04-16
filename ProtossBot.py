import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random
import math

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

class ProtossBot(sc2.BotAI):
    def __init__(self):
        self.warpgate_started = False
        self.upgrades = []

    async def has_ability(self, ability, unit):
        abilities = await self.get_available_abilities(unit)
        if ability in abilities:
            return True
        else:
            return False

    async def on_step(self, iteration):
        await self.distribute_workers(iteration)
        
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

        # 16 Probes por Nexus
        if self.workers.amount < self.units(NEXUS).amount*16 and nexus.is_idle and self.can_afford(PROBE):
            await self.do(nexus.train(PROBE))
            return

        # Precisamos de ao menos 1 Pylon, mas também precisamos de Pylons sempre que não tivermos supplies
        should_create_pylon = self.units(PYLON).amount == 0 or self.supply_left < 2
        
        amount_of_structures = self.units(GATEWAY).amount + self.units(CYBERNETICSCORE).amount + self.units(FLEETBEACON).amount + self.units(STARGATE).amount

        # Precisamos de 1 Pylon pra cada estrutura tbm
        should_create_pylon = should_create_pylon or self.units(PYLON).amount <= amount_of_structures

        # Por fim, analisamos se é possível construir um Pylon (ou se já temos algum em construção)
        should_create_pylon = should_create_pylon and not self.already_pending(PYLON) and self.can_afford(PYLON)
        
        int_rand = random.randint(0, 8)
        if should_create_pylon:
            await self.build(PYLON, near = nexus.position.towards(self.game_info.map_center, int_rand))
            return

        gateways_or_warp_gate_units = self.units(GATEWAY).amount + self.units(WARPGATE).amount 
        # Nosso foco é o Gateway, então precisamos construir pelo menos dois
        if gateways_or_warp_gate_units < 3 and self.units(PYLON).ready.amount > 0 and not self.already_pending(GATEWAY):
            pylon = self.units(PYLON).ready.random
            if pylon and self.can_afford(GATEWAY):
                await self.build(GATEWAY, near = pylon.position.towards(self.game_info.map_center, int_rand))
                return

        gateways_or_warp_gate_units_ready = self.units(GATEWAY).ready.amount + self.units(WARPGATE).ready.amount 
        # Em seguida, partimos para criar um Cybernetics Core
        if gateways_or_warp_gate_units_ready >= 2 and not self.units(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
            pylon = self.units(PYLON).ready.random
            if pylon and self.can_afford(CYBERNETICSCORE):
                await self.build(CYBERNETICSCORE, near = pylon.position.towards(self.game_info.map_center, int_rand))
                return

        # Para criar os Stalkers
        if self.units(CYBERNETICSCORE).ready.exists and self.can_afford(RESEARCH_WARPGATE) and not self.warpgate_started:
            ccore = self.units(CYBERNETICSCORE).ready.first
            self.warpgate_started = True
            await self.do(ccore(RESEARCH_WARPGATE))
            return
        
        # Atualizando Gateway em WarpGate
        # if self.units(GATEWAY).ready and not self.units(WARPGATE) and not self.already_pending(WARPGATE):
        #     gateway = self.units(GATEWAY).ready.first
        #     abilities = await self.get_available_abilities(gateway)
        #     if MORPH_WARPGATE in abilities and self.can_afford(MORPH_WARPGATE):
        #         await self.do(gateway(MORPH_WARPGATE))

        # Em seguida, criamos a Forge pra fazer os upgrades
        if gateways_or_warp_gate_units_ready >= 2 and not self.units(FORGE) and not self.already_pending(FORGE):
            pylon = self.units(PYLON).ready.random
            if pylon and self.can_afford(FORGE):
                await self.build(FORGE, near = pylon.position.towards(self.game_info.map_center, int_rand))
                return

        # Fazendo os upgrades
        if self.units(FORGE).ready:
            forge = self.units(FORGE).ready.first
            if self.can_afford(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1) and not FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1 in self.upgrades and forge.is_idle:
                self.upgrades.append(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1)
                await self.do(forge(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1))
                return

            elif self.can_afford(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1) and not FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1 in self.upgrades and forge.is_idle:
                self.upgrades.append(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1)
                await self.do(forge(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1))
                return
            
            elif self.can_afford(FORGERESEARCH_PROTOSSSHIELDSLEVEL1) and not FORGERESEARCH_PROTOSSSHIELDSLEVEL1 in self.upgrades and forge.is_idle:
                self.upgrades.append(FORGERESEARCH_PROTOSSSHIELDSLEVEL1)
                await self.do(forge(FORGERESEARCH_PROTOSSSHIELDSLEVEL1))
                return


        # # Criando a Stargate para a Mothership Core
        # if self.units(CYBERNETICSCORE).ready.exists and not self.units(STARGATE):
        #     pylon = self.units(PYLON).ready.random
        #     if pylon and self.can_afford(STARGATE):
        #         await self.build(STARGATE, near = pylon.position.towards(self.game_info.map_center, int_rand))

        # # Criando a Fleet Beacon para a Mothership Core
        # if self.units(STARGATE).ready.exists and not self.units(FLEETBEACON):
        #     pylon = self.units(PYLON).ready.random
        #     if pylon and self.can_afford(FLEETBEACON):
        #         await self.build(FLEETBEACON, near = pylon.position.towards(self.game_info.map_center, int_rand))

        # # Criando a Mothership
        # if self.units(FLEETBEACON).ready.exists and self.can_afford(MOTHERSHIPCORE) and not self.units(MOTHERSHIPCORE):
        #     await self.do(nexus.train(MOTHERSHIPCORE))

        # Damos prioridade aos Stalkers que são mais fortes, mas custam mais
        if gateways_or_warp_gate_units_ready >= 2 and self.units(STALKER).ready.amount <= 5 and self.warpgate_started:
            for gateway in self.units(GATEWAY).ready:
                if self.can_afford(STALKER) and gateway.is_idle:
                   await self.do(gateway.train(STALKER))
            
            # # Precisamos usar os Warp Gates para construir Stalkers também
            # if self.units(WARPGATE).ready:
            #     for warp_gate in self.units(WARPGATE).ready:
            #         if await self.has_ability(WARPGATETRAIN_STALKER, warp_gate) and self.can_afford(STALKER):
            #             await self.do(warp_gate.warp_in(STALKER, warp_gate.position.towards(self.game_info.map_center, int_rand)))
            # return

        # Já começamos a treinar Zealots, que são a base de nossa armada
        # Como Zealot usa só mineral, pode ser que tenhamos muito mineral e pouco gas
        should_create_zealot = self.units(ZEALOT).ready.amount <= 5 or self.minerals > 800
        if gateways_or_warp_gate_units_ready >= 2 and should_create_zealot:
            for gateway in self.units(GATEWAY).ready:
                if self.can_afford(ZEALOT) and gateway.is_idle:
                   await self.do(gateway.train(ZEALOT))
            
            # # Precisamos usar os Warp Gates para construir Zealots também
            # if self.units(WARPGATE).ready:
            #     for warp_gate in self.units(WARPGATE).ready:
            #         if await self.has_ability(WARPGATETRAIN_ZEALOT, warp_gate) and self.can_afford(ZEALOT):
            #             await self.do(warp_gate.warp_in(ZEALOT, warp_gate.position.towards(self.game_info.map_center, int_rand)))
            # return

        army_is_ready = (self.units(STALKER).ready.amount >= 5 and self.units(ZEALOT).ready.amount >= 5) or self.units(ZEALOT).ready.amount > 10
        
        # Atacando
        if army_is_ready:
            for zealot in self.units(ZEALOT).ready:
                has_targets = self.cached_known_enemy_units or self.cached_known_enemy_structures
                if has_targets:
                    targets = (self.cached_known_enemy_units | self.cached_known_enemy_structures).filter(lambda unit: unit.can_be_attacked)
                    target = targets.closest_to(zealot)
                    await self.do(zealot.attack(target))
                else:
                    await self.do(zealot.attack(self.enemy_start_locations[0]))

            for stalker in self.units(STALKER).ready.idle:
                has_targets = self.cached_known_enemy_units or self.cached_known_enemy_structures
                if has_targets:
                    targets = (self.cached_known_enemy_units | self.cached_known_enemy_structures).filter(lambda unit: unit.can_be_attacked)
                    target = targets.closest_to(stalker)
                    await self.do(stalker.attack(target))
                else:
                    await self.do(stalker.attack(self.enemy_start_locations[0]))

def main():
    sc2.run_game(
        sc2.maps.get("AcropolisLE"),
        [Bot(Race.Protoss, ProtossBot(), name="Botzada"), Computer(Race.Protoss, Difficulty.Medium)],
        realtime=False,
    )

if __name__ == "__main__":
    main()
