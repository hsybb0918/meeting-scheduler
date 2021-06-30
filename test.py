# @File        : test.py
# @Description :
# @Time        : 29 June, 2021
# @Author      : Cyan

import asyncio
import datetime
import time

from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade import quit_spade


class DummyAgent(Agent):
    class LongBehav(OneShotBehaviour):
        async def run(self):
            await asyncio.sleep(5)
            print("Long Behaviour has finished")

    class WaitingBehav(OneShotBehaviour):
        async def run(self):
            print(self.agent.behav)
            await self.agent.behav.join()  # this join must be awaited
            print("Waiting Behaviour has finished")

    async def setup(self):
        print("Agent starting . . .")
        self.behav = self.LongBehav()
        self.add_behaviour(self.behav)
        self.behav2 = self.WaitingBehav()
        self.add_behaviour(self.behav2)


if __name__ == "__main__":
    # dummy = DummyAgent('meeting-bob@404.city', 'meeting-bob')
    # future = dummy.start()
    # future.result()
    #
    # while True:
    #     pass

    # dummy.behav2.join()  # this join must not be awaited
    #
    # print("Stopping agent.")
    # dummy.stop()
    #
    # quit_spade()

    l = [1, 2, 3]
    print(len(l))