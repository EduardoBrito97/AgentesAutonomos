import random
from sc2.constants import *

class Observadores():
    def __init__(self, protoss_bot):
        self.bot = protoss_bot

    async def do_work(self):
        return