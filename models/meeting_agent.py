# @File        : meeting_agent.py
# @Description :
# @Time        : 15 June, 2021
# @Author      : Cyan
from spade import agent
from spade.behaviour import CyclicBehaviour

from models.user_calendar import UserCalendar


class MeetingAgent(agent.Agent):
    user_calendar = UserCalendar()

    class RequestMeeting(CyclicBehaviour):
        async def on_start(self):
            pass

        async def run(self):
            pass

    async def setup(self):
        print("Hello World! I'm agent {}".format(str(self.jid)))
        self.add_behaviour(self.RequestMeeting())


if __name__ == "__main__":
    host_agent = MeetingAgent("meeting-bob@404.city", "meeting-bob")
    future_host = host_agent.start()
    future_host.result()

    participant_agent = MeetingAgent("meeting-alice@404.city", "meeting-alice")
    future_participant = participant_agent.start()
    future_participant.result()

    # "meeting-alice@404.city", "meeting-alice"
    # "meeting-bob@404.city", "meeting-bob"
