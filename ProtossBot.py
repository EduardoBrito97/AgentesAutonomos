import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random
import math
import logging

import sc2
from Trabalhadores import Trabalhadores
from Oraculo import Oraculo
from Soldados import Soldados
from Observadores import Observadores
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer

class ProtossBot(sc2.BotAI):
    def __init__(self):
        self.oraculo = Oraculo(self)
        self.trabalhadores = Trabalhadores(self)
        self.soldados = Soldados(self)
        self.observadores = Observadores(self)
        self.attack_in_course = False

    async def has_ability(self, ability, unit):
        abilities = await self.get_available_abilities(unit)
        if ability in abilities:
            return True
        else:
            return False

    async def has_upgrade(self, upgrade):
        return upgrade in self.oraculo.upgrades

    async def call_for_attack(self):
        self.attack_in_course = True

    async def retreat(self):
        self.attack_in_course = False

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("GL HF")

        try:
            await self.oraculo.do_work()
            await self.observadores.do_work()
            await self.trabalhadores.do_work(iteration)
            await self.soldados.do_work(iteration)

        except Exception as e:
            logging.error("Error: " + str(e))

def main():
    sc2.run_game(
        sc2.maps.get("AcropolisLE"),
        [Bot(Race.Protoss, ProtossBot(), name="Botzada"), Computer(Race.Protoss, Difficulty.Harder)],
        realtime=False,
    )

if __name__ == "__main__":
    main()
