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

        amount_of_structures = bot.units(GATEWAY).amount + bot.units(CYBERNETICSCORE).amount + bot.units(FLEETBEACON).amount + bot.units(STARGATE).amount
       
        # Precisamos de ao menos 1 Pylon, mas também precisamos de Pylons sempre que não tivermos supplies
        should_create_pylon = bot.units(PYLON).amount == 0 or bot.supply_left < 5

        # Precisamos de 1 Pylon pra cada estrutura tbm
        should_create_pylon = should_create_pylon or bot.units(PYLON).amount <= amount_of_structures

        # Por fim, analisamos se é possível construir um Pylon (ou se já temos algum em construção)
        should_create_pylon = should_create_pylon and not bot.already_pending(PYLON) and bot.can_afford(PYLON)

        pos = await self.find_place_to_build(PYLON)
        closest_structure_distance = self.bot.units.filter(lambda u: u.is_structure).closest_to(pos).distance_to(pos)
        if should_create_pylon and closest_structure_distance > 3:
            await bot.build(PYLON, near = pos)

    async def find_place_to_build(self, structure_to_build):
        structure = self.bot.units(NEXUS).random
        if self.bot.units(PYLON).ready and structure_to_build != PYLON:
            structure = self.bot.units.filter(lambda unit: unit.is_structure).random

        amount_of_structures = self.bot.units.filter(lambda unit: unit.is_structure).amount

        rand_num = random.randint(4, 4 + amount_of_structures % 10)

        if amount_of_structures % 3 == 0:
            target = self.bot.game_info.map_center
        elif amount_of_structures % 3 == 1:
            target = self.bot.start_location
        else:
            target = self.bot.enemy_start_locations[0]

        return structure.position.towards_with_random_angle(target, rand_num)

    async def build_structure(self, structure):
        if not self.bot.already_pending(structure):
            pos = await self.find_place_to_build(structure)
            closest_structure_distance = self.bot.units.filter(lambda u: u.is_structure).closest_to(pos).distance_to(pos)
            if self.bot.can_afford(structure) and closest_structure_distance > 3:
                await self.bot.build(structure, near = pos)
                return True
        return False

    async def build_proxy_pylon(self):
        enemy_location = self.bot.enemy_start_locations[0]
        proxy_built = False

        if self.bot.units(PYLON).ready:
            pylon_closest_to_enemy = self.bot.units(PYLON).closest_to(enemy_location)
            distance_to_enemy = pylon_closest_to_enemy.distance_to(enemy_location)
            if distance_to_enemy <= 80:
                proxy_built = True

        if self.bot.units(PROBE).ready and not proxy_built:
            worker = self.bot.units(PROBE).ready.closest_to(enemy_location)
            distance_to_enemy = worker.distance_to(enemy_location)
            soldier_to_follow = (self.bot.units(ZEALOT).ready | self.bot.units(STALKER).ready).closest_to(enemy_location)

            if distance_to_enemy <= 70 and self.bot.can_afford(PYLON) and not self.bot.already_pending(PYLON):
                await self.bot.build(PYLON, near = worker.position)
            else:
                await self.bot.do(worker.move(soldier_to_follow.position.towards(self.bot.start_location, 9)))
        
    async def expand_if_needed(self):
        all_minerals_near_base = [
                mineral
                for mineral in self.bot.state.mineral_field
                if any(mineral.distance_to(base) <= 8 for base in self.bot.townhalls.ready)
            ]
        desired_num_of_minerals = self.bot.units(NEXUS).amount * 2

        if len(all_minerals_near_base) < desired_num_of_minerals:
            await self.bot.set_save_mineral(True)

        if (self.bot.townhalls.ready.amount + self.bot.already_pending(NEXUS) < 3 or len(all_minerals_near_base) < desired_num_of_minerals) and self.bot.can_afford(NEXUS):
            await self.bot.expand_now()
            await self.bot.set_save_mineral(False)
            return True
        return False

    async def do_work(self, iteration):
        bot = self.bot

        if iteration % 20 == 0 and self.bot.vespene < 400:
            await self.bot.distribute_workers()
        elif iteration % 20 == 0:
            await self.bot.distribute_workers(1000)

        # Precisamos expandir pra ter pelo menos dois nexus (e mais quanto necessário esteja acabando os recursos)
        if await self.expand_if_needed():
            return

        # Caso a gente já tenha começado o ataque, criar um Pylon pra gente conseguir produzir unidade perto do inimigo
        if bot.attack_in_course and iteration % 5:
            await self.build_proxy_pylon()

        # Foco em produzir assimilator perto de todos os nexus
        await self.build_gas_assimilators()
        
        # Precisamos de Pylons
        await self.build_pylons()
        
        gateways_or_warp_gate_units = bot.units(GATEWAY).amount + bot.units(WARPGATE).amount 
        # Nosso foco é o Gateway, então precisamos construir pelo menos 2 para começar. Mais tarde construímos mais
        if gateways_or_warp_gate_units < 2 and bot.units(PYLON).ready.amount > 0 :
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
        
        lv_updates_ready = await bot.has_upgrade(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1) and await bot.has_upgrade(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1) and await bot.has_upgrade(FORGERESEARCH_PROTOSSSHIELDSLEVEL1)
        if bot.units(FORGE).ready and not bot.units(TWILIGHTCOUNCIL) and not bot.already_pending(TWILIGHTCOUNCIL) and lv_updates_ready:
            await self.build_structure(TWILIGHTCOUNCIL)
            return

        # Criando a Stargate para a Mothership
        if bot.units(CYBERNETICSCORE).ready.exists and not bot.units(STARGATE):
            await self.build_structure(STARGATE)
            return

        # Criando a Fleet Beacon para a Mothership
        if bot.units(STARGATE).ready.exists and not bot.units(FLEETBEACON):
            await self.build_structure(FLEETBEACON)
            return
        # Agora construimos mais alguns Gateways para podermos produzir mais tropas
        if gateways_or_warp_gate_units < 5 and bot.units(PYLON).ready.amount > 0 :
            await self.build_structure(GATEWAY)
            return

        # Agora construimos mais alguns Gateways para podermos produzir mais tropas
        if gateways_or_warp_gate_units < 7 and bot.units(PYLON).ready.amount > 0 :
            await self.build_structure(GATEWAY)
            return

        # Por fim, precisamos de defesas
        if gateways_or_warp_gate_units_ready >= 7 and bot.units(PHOTONCANNON).ready.amount < 3 and not bot.already_pending(PHOTONCANNON):
            nexus = bot.units(NEXUS).closest_to(bot.enemy_start_locations[0])
            if nexus and bot.can_afford(PHOTONCANNON):
                await bot.build(PHOTONCANNON, near = nexus.position.towards_with_random_angle(bot.enemy_start_locations[0], 6).to2.random_on_distance(4))
                return

        # Depois de construir tudo, a gente precisa de mais população
        if bot.supply_left < 8 and bot.units(PYLON).amount - bot.units(PYLON).ready.amount < 3 and bot.units(PHOTONCANNON).ready.amount >= 3 and bot.supply_cap < 200:
            await self.build_structure(PYLON)
            return

        # Por fim, se a gente tem recurso sobrando, taca canhão pra defesa
        if bot.units(PHOTONCANNON).ready.amount >= 3 and self.bot.minerals > 1500 and self.bot.vespene > 1000 and bot.units(PHOTONCANNON).ready.amount < 8:
            nexus = bot.units(NEXUS).closest_to(bot.enemy_start_locations[0])
            if nexus and bot.can_afford(PHOTONCANNON):
                pos = await self.find_place_to_build(PHOTONCANNON)
                await bot.build(PHOTONCANNON, near = pos)