# @File        : meeting_agent.py
# @Description :
# @Time        : 15 June, 2021
# @Author      : Cyan
import asyncio
import json
import time

from spade import agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour, OneShotBehaviour, FSMBehaviour
from spade.message import Message
from spade.template import Template

from models.user_calendar import UserCalendar, ScheduledMeeting


class MeetingAgent(agent.Agent):
    user_calendar = UserCalendar()

    is_host = False
    proposed_meeting = None

    class HostMeeting(PeriodicBehaviour):
        async def run(self):
            if self.agent.is_host:
                meeting_json = json.dumps(self.agent.proposed_meeting, default=lambda o: o.__dict__)
                print('{} -> propose a meeting: {}'.format(self.agent.jid, meeting_json))
                self.agent.add_behaviour(self.agent.ProposeRequest())
                self.agent.is_host = False

    class ProposeRequest(OneShotBehaviour):
        async def run(self):
            request_msg = Message()
            request_msg.body = json.dumps(self.agent.proposed_meeting, default=lambda o: o.__dict__)
            request_msg.thread = 'simple-match'
            request_msg.set_metadata('performative', 'query')

            for to in self.agent.proposed_meeting.guest_agents:
                request_msg.to = to
                await self.send(request_msg)
                print('{} -> send the meeting request to {}'.format(self.agent.jid, to))

            self.agent.add_behaviour(self.agent.ProposeCounterproposal())

    class ProposeCounterproposal(CyclicBehaviour):

        async def on_start(self):
            print('counterproposal start')

        async def run(self):
            request_msg_mt = Template()
            request_msg_mt.thread = 'simple-match-reply'
            self.set_template(request_msg_mt)

            message_count = len(self.agent.proposed_meeting.guest_agents)
            agree_count = 0

            if self.mailbox_size() == message_count:
                for i in range(message_count):
                    reply_msg_receive = await self.receive()

                    if reply_msg_receive.get_metadata('performative') == 'agree':
                        agree_count += 1

                if agree_count != message_count:
                    # counterproposal
                    pass
                    # request_msg = Message()
                    # request_msg.body = json.dumps(self.agent.proposed_meeting, default=lambda o: o.__dict__)
                    # request_msg.thread = 'simple-match'
                    # request_msg.set_metadata('performative', 'query')
                else:
                    # success
                    print('{} -> confirm the meeting'.format(self.agent.jid))
                    self.agent.add_behaviour(self.agent.ProposeConfirmation())
                self.kill()

        async def on_end(self):
            print('counterproposal end')

    class ProposeVoting(CyclicBehaviour):

        async def run(self):
            pass

    class ProposeConfirmation(OneShotBehaviour):
        async def on_start(self):
            print('confirm meeting start')

        async def run(self):
            confirm_msg = Message()
            confirm_msg.thread = 'meeting-confirmation'
            confirm_msg.set_metadata('performative', 'inform')

            for to in self.agent.proposed_meeting.guest_agents:
                confirm_msg.to = to
                await self.send(confirm_msg)
                print('{} -> send the meeting confirmation to {}'.format(self.agent.jid, to))

        async def on_end(self):
            print('confirm meeting end')

    class ResponseRequest(CyclicBehaviour):
        async def on_start(self):
            print('response meeting start')

        async def run(self):
            request_msg_mt = Template()
            request_msg_mt.thread = 'simple-match'
            request_msg_mt.set_metadata('performative', 'query')
            self.set_template(request_msg_mt)

            if self.mailbox_size() == 1:
                # request_msg_receive = await self.receive()
                # if request_msg_receive is not None:
                request_msg_receive = await self.receive()
                print('{} -> receive the meeting request from {}'.format(self.agent.jid, request_msg_receive.sender))
                print('{} -> requested meeting: {}'.format(self.agent.jid, request_msg_receive.body))

                meeting_dict = json.loads(request_msg_receive.body)

                meeting = ScheduledMeeting(meeting_dict['month'], meeting_dict['day'], meeting_dict['year'])
                meeting.set_time_slots_from_list(meeting_dict['time_slots'])
                meeting.set_host(meeting_dict['host_agent'])
                meeting.set_guests_from_list(meeting_dict['guest_agents'])
                meeting.set_information(meeting_dict['subject'], meeting_dict['location'], meeting_dict['description'])
                self.agent.proposed_meeting = meeting

                request_msg_reply = Message()
                request_msg_reply.to = str(request_msg_receive.sender)
                request_msg_reply.thread = 'simple-match-reply'
                request_msg_reply.set_metadata('performative', 'agree')

                # request_msg_reply = request_msg_receive.make_reply()
                # request_msg_reply.set_metadata('performative', 'agree')
                # request_msg_reply.set_metadata('stage', 'simple-match-reply')
                await self.send(request_msg_reply)

                # await self.send(request_msg_reply)
                # if time is available
                self.agent.add_behaviour(self.agent.ResponseCounterproposal())
                self.kill()

        async def on_end(self):
            print('response meeting end')

    class ResponseCounterproposal(CyclicBehaviour):
        async def on_start(self):
            print('response counterproposal start')

        async def run(self):
            request_msg_mt = Template()
            request_msg_mt.thread = 'simple-match'
            request_msg_mt.set_metadata('performative', 'query')
            self.set_template(request_msg_mt)

        async def on_end(self):
            print('response counterproposal end')

    class ResponseVoting(CyclicBehaviour):
        async def on_start(self):
            print('response counterproposal start')

        async def run(self):
            request_msg_mt = Template()
            request_msg_mt.thread = 'simple-match'
            request_msg_mt.set_metadata('performative', 'query')
            self.set_template(request_msg_mt)

        async def on_end(self):
            print('response counterproposal end')

    class ResponseConfirmation(CyclicBehaviour):
        async def on_start(self):
            print('response counterproposal start')

        async def run(self):
            request_msg_mt = Template()
            request_msg_mt.thread = 'simple-match'
            request_msg_mt.set_metadata('performative', 'query')
            self.set_template(request_msg_mt)

        async def on_end(self):
            print('response counterproposal end')

    async def setup(self):
        print('{}: start'.format(str(self.jid)))

        self.add_behaviour(self.HostMeeting(period=2))
        self.add_behaviour(self.ResponseRequest())

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
