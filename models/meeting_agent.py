# @File        : meeting_agent.py
# @Description :
# @Time        : 15 June, 2021
# @Author      : Cyan
import asyncio
import json

from spade import agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour, OneShotBehaviour, FSMBehaviour
from spade.message import Message
from spade.template import Template

from models.user_calendar import UserCalendar, ScheduledMeeting


class MeetingAgent(agent.Agent):
    user_calendar = UserCalendar()

    is_host = False
    proposed_meeting = None

    class ProposeMeeting(PeriodicBehaviour):
        async def run(self):
            if self.agent.is_host:
                print('{}: propose a meeting'.format(self.agent.jid))
                print('{}: \'{}\''.format(self.agent.jid, json.dumps(self.agent.proposed_meeting)))
                self.agent.add_behaviour(self.agent.RequestMeeting())
                self.agent.is_host = False

    class RequestMeeting(OneShotBehaviour):
        async def run(self):
            request_msg = Message()
            request_msg.body = 'meeting request'
            request_msg.set_metadata('performative', 'cfp')

            for to in self.agent.proposed_meeting.guest_agents:
                request_msg.to = to
                await self.send(request_msg)
                print('{}: send the meeting request to {}'.format(self.agent.jid, to))


    class ResponseMeeting(CyclicBehaviour):
        async def run(self):
            request_msg_mt = Template()
            request_msg_mt.set_metadata('performative', 'cfp')
            self.set_template(request_msg_mt)

            request_msg_receive = await self.receive()
            if request_msg_receive is not None:
                print('{}: receive the meeting request from {}'.format(self.agent.jid, request_msg_receive.sender))
                print(request_msg_receive.body)

    async def setup(self):
        print('{}: start'.format(str(self.jid)))

        self.add_behaviour(self.ProposeMeeting(period=2))
        self.add_behaviour(self.ResponseMeeting())

    def propose_meeting(self, meeting):
        self.proposed_meeting = meeting
        self.is_host = True


if __name__ == '__main__':
    host_agent = MeetingAgent('meeting-alice@404.city', 'meeting-alice')
    host_agent.start()

    guest_agent_1 = MeetingAgent('meeting-bob@404.city', 'meeting-bob')
    guest_agent_1.start()

    guest_agent_2 = MeetingAgent('meeting-calvin@404.city', 'meeting-calvin')
    guest_agent_2.start()
