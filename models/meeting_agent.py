# @File        : meeting_agent.py
# @Description :
# @Time        : 15 June, 2021
# @Author      : Cyan
import asyncio
import json
from collections import Counter

from spade import agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template

from models.user_calendar import UserCalendar, ScheduledMeeting
from models.utils import get_config


class MeetingAgent(agent.Agent):
    user_calendar = None

    is_host = None
    proposed_meeting = None

    class ProposeRequest(CyclicBehaviour):
        async def on_start(self):
            print('request start')

        async def run(self):
            # if the agent propose a meeting
            if self.agent.is_host:
                print('{} -> proposed meeting: {}'.format(self.agent.jid, self.agent.proposed_meeting))

                # START simple match process
                meeting_json = json.dumps(self.agent.proposed_meeting, default=lambda o: o.__dict__)
                meeting_load = json.loads(meeting_json)
                print('{} -> {}'.format(self.agent.jid, meeting_load))

                # prepare message
                request_msg = Message()
                request_msg.body = meeting_json
                request_msg.thread = 'simple-match'
                request_msg.set_metadata('performative', 'query')

                # send message to all guest agents
                for to in self.agent.proposed_meeting.guest_agents:
                    request_msg.to = to
                    await self.send(request_msg)
                    print('{} -> send the meeting request to {}'.format(self.agent.jid, to))

                self.agent.is_host = False
                # add next behavior
                self.agent.add_behaviour(self.agent.ProposeCounterproposal())
                # kill the behaviour
                self.kill()

    class ProposeCounterproposal(CyclicBehaviour):
        async def run(self):
            reply_msg_mt = Template()
            reply_msg_mt.thread = 'simple-match-reply'
            self.set_template(reply_msg_mt)

            # message reply count
            message_count = len(self.agent.proposed_meeting.guest_agents)
            agree_count = 0

            # receive all replies
            if self.mailbox_size() == message_count:
                for i in range(message_count):
                    reply_msg_receive = await self.receive()

                    print('{} -> reply from {}: {}'.format(self.agent.jid, reply_msg_receive.sender,
                                                           reply_msg_receive.get_metadata('performative')))

                    if reply_msg_receive.get_metadata('performative') == 'agree':
                        agree_count += 1

                if agree_count != message_count:
                    # propose counterproposal
                    print('{} -> propose the counterproposal'.format(self.agent.jid))

                    counterproposal_msg = Message()
                    counterproposal_msg.thread = 'counterproposal-process'
                    counterproposal_msg.set_metadata('performative', 'query')

                    for to in self.agent.proposed_meeting.guest_agents:
                        counterproposal_msg.to = to
                        await self.send(counterproposal_msg)
                        print('{} -> propose the counterproposal to {}'.format(self.agent.jid, to))

                    # add next behaviour
                    self.agent.add_behaviour(self.agent.ProposeVoting())
                else:
                    # success, confirm the meeting
                    print('{} -> send the meeting confirmation'.format(self.agent.jid))

                    success_msg = Message()
                    success_msg.thread = 'counterproposal-process'
                    success_msg.set_metadata('performative', 'inform')

                    for to in self.agent.proposed_meeting.guest_agents:
                        success_msg.to = to
                        await self.send(success_msg)
                        print('{} -> send the meeting confirmation to {}'.format(self.agent.jid, to))

                    # add the proposed meeting and clear the variable
                    self.agent.add_meeting(self.agent.proposed_meeting)
                    self.agent.proposed_meeting = None

                    # back to the first behaviour
                    self.agent.add_behaviour(self.agent.ProposeRequest())

                # kill this behaviour
                self.kill()

    class ProposeVoting(CyclicBehaviour):
        async def run(self):
            reply_msg_mt = Template()
            reply_msg_mt.thread = 'counterproposal-process-reply'
            self.set_template(reply_msg_mt)

            # message reply count
            message_count = len(self.agent.proposed_meeting.guest_agents)

            # receive all replies
            if self.mailbox_size() == message_count:
                counterproposals = []

                for i in range(message_count):
                    reply_msg_receive = await self.receive()

                    counterproposal = json.loads(reply_msg_receive.body)
                    counterproposal = {int(k): v for k, v in counterproposal.items()}
                    counterproposals.append(counterproposal)

                    print('{} -> reply from {}: {}'.format(self.agent.jid, reply_msg_receive.sender, counterproposal))

                counterproposals.append(self.agent.find_counterproposal_slots())
                best_slot = self.agent.check_counterproposal_availability(counterproposals)

                if best_slot is None:
                    # propose voting
                    print('{} -> propose the voting'.format(self.agent.jid))

                    voting_msg = Message()
                    voting_msg.thread = 'voting-process'
                    voting_msg.set_metadata('performative', 'query')

                    # prepare voting options
                    print('{} -> voting slots: {}'.format(self.agent.jid, list(self.agent.find_voting_slots())))

                    voting_msg.body = json.dumps(list(self.agent.find_voting_slots().keys()))

                    for to in self.agent.proposed_meeting.guest_agents:
                        voting_msg.to = to
                        await self.send(voting_msg)
                        print('{} -> propose the voting to {}'.format(self.agent.jid, to))

                    # add next behaviour
                    self.agent.add_behaviour(self.agent.ProposeConfirmation())
                else:
                    # success, confirm the meeting
                    print('{} -> send the meeting confirmation at slot {}'.format(self.agent.jid, best_slot))

                    success_msg = Message()
                    success_msg.thread = 'voting-process'
                    success_msg.set_metadata('performative', 'inform')

                    for to in self.agent.proposed_meeting.guest_agents:
                        success_msg.to = to
                        await self.send(success_msg)
                        print('{} -> send the meeting confirmation to {}'.format(self.agent.jid, to))

                    # add the proposed meeting and clear the variable
                    self.agent.add_meeting(self.agent.proposed_meeting)
                    self.agent.proposed_meeting = None

                    # back to the first behaviour
                    self.agent.add_behaviour(self.agent.ProposeRequest())

                    # kill this behaviour
                self.kill()

    class ProposeConfirmation(CyclicBehaviour):
        async def run(self):
            reply_msg_mt = Template()
            reply_msg_mt.thread = 'voting-process-reply'
            self.set_template(reply_msg_mt)

            # message reply count
            message_count = len(self.agent.proposed_meeting.guest_agents)

            # receive all replies
            if self.mailbox_size() == message_count:

                voting_results = []

                for i in range(message_count):
                    reply_msg_receive = await self.receive()

                    voting_result = json.loads(reply_msg_receive.body)
                    voting_result = {int(k): v for k, v in voting_result.items()}
                    voting_results.append(voting_result)

                    print('{} -> reply from {}: {}'.format(self.agent.jid, reply_msg_receive.sender, voting_result))

                voting_results.append(self.agent.find_voting_slots())
                best_slot = self.agent.check_voting_availability(voting_results)

                final_msg = Message()
                final_msg.thread = 'final-process'

                if best_slot is None:
                    # failed to schedule the meeting
                    print('{} -> failed to schedule the meeting'.format(self.agent.jid))

                    final_msg.set_metadata('performative', 'failure')

                    # add next behaviour
                    self.agent.add_behaviour(self.agent.ProposeRequest())
                else:
                    # success, confirm the meeting
                    print('{} -> schedule the meeting at slot {}'.format(self.agent.jid, best_slot))

                    final_msg.set_metadata('performative', 'inform')

                    # add the proposed meeting
                    self.agent.add_meeting(self.agent.proposed_meeting)

                    # back to the first behaviour
                    self.agent.add_behaviour(self.agent.ProposeRequest())

                for to in self.agent.proposed_meeting.guest_agents:
                    final_msg.to = to
                    await self.send(final_msg)
                    print('{} -> send the final decision to {}'.format(self.agent.jid, to))

                # clear the variable
                self.agent.proposed_meeting = None

                # kill this behaviour
                self.kill()

            # for to in self.agent.proposed_meeting.guest_agents:
            #     confirm_msg.to = to
            #     await self.send(confirm_msg)
            #     print('{} -> send the meeting confirmation to {}'.format(self.agent.jid, to))

        async def on_end(self):
            print('confirm meeting end')

    class ResponseRequest(CyclicBehaviour):
        async def on_start(self):
            print('response request start')

        async def run(self):
            # set request message template
            request_msg_mt = Template()
            request_msg_mt.thread = 'simple-match'
            request_msg_mt.set_metadata('performative', 'query')
            self.set_template(request_msg_mt)

            # if receive the request
            if self.mailbox_size() == 1:
                request_msg_receive = await self.receive()
                print('{} -> receive the meeting request from {}'.format(self.agent.jid, request_msg_receive.sender))

                # create the meeting and store locally
                meeting_dict = json.loads(request_msg_receive.body)

                meeting = ScheduledMeeting(meeting_dict['month'], meeting_dict['day'], meeting_dict['year'])
                meeting.set_time_slots_from_list(meeting_dict['time_slots'])
                meeting.set_host(meeting_dict['host_agent'])
                meeting.set_guests_from_list(meeting_dict['guest_agents'])
                meeting.set_information(meeting_dict['subject'], meeting_dict['location'], meeting_dict['description'])
                self.agent.proposed_meeting = meeting

                print('{} -> requested meeting: {}'.format(self.agent.jid, self.agent.proposed_meeting))

                # prepare reply message
                request_msg_reply = Message()
                request_msg_reply.to = str(request_msg_receive.sender)
                request_msg_reply.thread = 'simple-match-reply'

                # check if the time is available
                if self.agent.check_time_availability():
                    print('{} -> requested time is available'.format(self.agent.jid))
                    request_msg_reply.set_metadata('performative', 'agree')
                else:
                    print('{} -> requested time is unavailable'.format(self.agent.jid))
                    request_msg_reply.set_metadata('performative', 'refuse')

                # send the reply message
                await self.send(request_msg_reply)

                # add new behaviour
                self.agent.add_behaviour(self.agent.ResponseCounterproposal())
                # kill this behaviour
                self.kill()

        async def on_end(self):
            print('{} -> response request behavior end'.format(self.agent.jid))

    class ResponseCounterproposal(CyclicBehaviour):
        async def run(self):
            counterproposal_msg_mt = Template()
            counterproposal_msg_mt.thread = 'counterproposal-process'
            self.set_template(counterproposal_msg_mt)

            # receive the counterproposal message
            if self.mailbox_size() == 1:
                counterproposal_msg_receive = await self.receive()
                counterproposal_metadata = counterproposal_msg_receive.get_metadata('performative')

                if counterproposal_metadata == 'query':
                    # counterproposal
                    print('{} -> response counterproposal'.format(self.agent.jid))

                    # prepare reply message
                    counterproposal_msg_reply = Message()
                    counterproposal_msg_reply.to = str(counterproposal_msg_receive.sender)
                    counterproposal_msg_reply.thread = 'counterproposal-process-reply'

                    counterproposal_msg_reply.body = json.dumps(self.agent.find_counterproposal_slots())

                    print('{} -> {}'.format(self.agent.jid, json.dumps(self.agent.find_counterproposal_slots())))

                    # send the reply message
                    await self.send(counterproposal_msg_reply)

                    # add response voting behaviour
                    self.agent.add_behaviour(self.agent.ResponseVoting())
                elif counterproposal_metadata == 'inform':
                    # success
                    print('{} -> receive the meeting confirmation'.format(self.agent.jid))

                    # add the proposed meeting and clear the variable
                    self.agent.add_meeting(self.agent.proposed_meeting)
                    self.agent.proposed_meeting = None

                    # back to the first behaviour
                    self.agent.add_behaviour(self.agent.ResponseRequest())

                self.kill()

    class ResponseVoting(CyclicBehaviour):
        async def run(self):
            voting_msg_mt = Template()
            voting_msg_mt.thread = 'voting-process'
            self.set_template(voting_msg_mt)

            # receive the voting message
            if self.mailbox_size() == 1:
                voting_msg_receive = await self.receive()
                voting_metadata = voting_msg_receive.get_metadata('performative')

                if voting_metadata == 'query':
                    # voting
                    print('{} -> response voting'.format(self.agent.jid))

                    voting_slots = json.loads(voting_msg_receive.body)

                    slot_num = len(self.agent.proposed_meeting.time_slots)
                    slot_preference = self.agent.user_calendar.global_slot_preference
                    # start_slot = self.agent.proposed_meeting.time_slots[0]

                    return_voting = {}
                    for slot in voting_slots:
                        is_available = True
                        total_preference = 0
                        for i in range(slot_num):
                            total_preference += slot_preference[slot + i]
                            if slot_preference[slot + i] == 0:
                                is_available = False


                        if is_available:
                            return_voting[slot] = total_preference / slot_num
                        else:
                            return_voting[slot] = 0


                    # prepare reply message
                    voting_msg_reply = Message()
                    voting_msg_reply.to = str(voting_msg_receive.sender)
                    voting_msg_reply.thread = 'voting-process-reply'

                    voting_msg_reply.body = json.dumps(return_voting)

                    print('{} -> returned voting: {}'.format(self.agent.jid, json.dumps(return_voting)))

                    # send the reply message
                    await self.send(voting_msg_reply)

                    # add next behaviour
                    self.agent.add_behaviour(self.agent.ResponseConfirmation())

                elif voting_metadata == 'inform':
                    # success
                    print('{} -> receive the meeting confirmation'.format(self.agent.jid))

                    # add the proposed meeting and clear the variable
                    self.agent.add_meeting(self.agent.proposed_meeting)
                    self.agent.proposed_meeting = None

                    # back to the first behaviour
                    self.agent.add_behaviour(self.agent.ResponseRequest())

                self.kill()

        async def on_end(self):
            print('response counterproposal end')

    class ResponseConfirmation(CyclicBehaviour):
        async def on_start(self):
            print('response confirmation start')

        async def run(self):
            final_msg_mt = Template()
            final_msg_mt.thread = 'final-process'
            self.set_template(final_msg_mt)

            # receive the voting message
            if self.mailbox_size() == 1:
                final_msg_receive = await self.receive()

                decision = final_msg_receive.get_metadata('performative')

                if decision == 'failure':
                    print('{} -> failed to schedule the meeting'.format(self.agent.jid))
                elif decision == 'inform':
                    print('{} -> success to schedule the meeting'.format(self.agent.jid))

                    # add the proposed meeting and clear the variable
                    # todo
                    self.agent.add_meeting(self.agent.proposed_meeting)

                self.agent.proposed_meeting = None


                # back to the first behaviour
                self.agent.add_behaviour(self.agent.ResponseRequest())
                self.kill()


        async def on_end(self):
            print('response confirmation end')

    def __init__(self, jid, password, verify_security=False):
        super().__init__(jid, password, verify_security)

        self.user_calendar = UserCalendar()
        self.is_host = False

    async def setup(self):
        # start the agent
        print('{}: start'.format(str(self.jid)))

        # add two types of behaviours
        self.add_behaviour(self.ProposeRequest())
        self.add_behaviour(self.ResponseRequest())

    def add_meeting(self, meeting):
        self.user_calendar.scheduled_meetings.append(meeting)
        print('{} -> schedule the meeting successfully'.format(self.jid))
        print('{} -> now the number of meetings: {}'.format(self.jid, len(self.user_calendar.scheduled_meetings)))

    def propose_meeting(self, meeting):
        self.proposed_meeting = meeting
        self.is_host = True

    def check_time_availability(self):
        proposed_time_slots = self.proposed_meeting.time_slots
        return self.user_calendar.check_time_slots(proposed_time_slots)

    def set_time_slots_preference(self, dictionary):
        for slot, pref in dictionary.items():
            self.user_calendar.global_slot_preference[slot] = pref

    def find_counterproposal_slots(self):
        # consider proposed meeting and no more than 5
        available_slots = {}

        proposed_start = self.proposed_meeting.time_slots[0]
        slot_num = len(self.proposed_meeting.time_slots)
        for start in range(int(get_config('default', 'slot_division')) - slot_num + 1):
            is_available = True
            preference_total = 0
            for i in range(slot_num):
                preference_total += self.user_calendar.global_slot_preference[start + i]

                if self.user_calendar.global_slot_preference[start + i] == 0:
                    is_available = False

            if is_available:
                preference_avg = round(preference_total / slot_num, 1)
                distance = abs(start - proposed_start)
                counter_distance = int(get_config('default', 'slot_division')) - distance

                available_slots[start] = [preference_avg, counter_distance]

        # sort and choose (5 + slot_num) slot range
        return_slots = {}

        sorted_slots = sorted(available_slots.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True)
        for i in range(5 + slot_num):
            return_slots[sorted_slots[i][0]] = sorted_slots[i][1][0]

        return return_slots

    def check_counterproposal_availability(self, counterproposals):
        participant_num = len(self.proposed_meeting.guest_agents) + 1
        proposed_start = self.proposed_meeting.time_slots[0]

        slots_all = []
        for counterproposal in counterproposals:
            slots_all.extend(counterproposal.keys())

        counter_all = Counter(slots_all)
        print(counter_all)

        slots_common = [int(k) for k, v in counter_all.items() if v >= participant_num]

        print(counterproposals)
        print(slots_common)

        if len(slots_common) == 0:
            return None
        elif len(slots_common) == 1:
            return slots_common[0]
        else:
            best_preference = 0
            best_distance = int(get_config('default', 'slot_division')) * participant_num
            best_slot = None

            for slot in slots_common:
                cur_preference = 0

                for i in range(participant_num):
                    cur_preference += counterproposals[i][slot]

                cur_distance = abs(slot - proposed_start)

                print(slot, cur_preference, cur_distance)

                if cur_preference > best_preference:
                    best_preference = cur_preference
                    best_distance = cur_distance
                    best_slot = slot
                elif cur_preference == best_preference and cur_distance < best_distance:
                    best_distance = cur_distance
                    best_slot = slot

            # return best_slot
            return None

    def find_voting_slots(self):
        available_slots = {}

        proposed_start = self.proposed_meeting.time_slots[0]
        slot_num = len(self.proposed_meeting.time_slots)
        for start in range(int(get_config('default', 'slot_division')) - slot_num + 1):
            is_available = True
            preference_total = 0
            for i in range(slot_num):
                preference_total += self.user_calendar.global_slot_preference[start + i]

                if self.user_calendar.global_slot_preference[start + i] == 0:
                    is_available = False

            if is_available:
                preference_avg = round(preference_total / slot_num, 1)
                distance = abs(start - proposed_start)
                counter_distance = int(get_config('default', 'slot_division')) - distance

                available_slots[start] = [preference_avg, counter_distance]

        # sort and choose 10 slot range
        return_slots = {}

        sorted_slots = sorted(available_slots.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True)
        for i in range(10):
            return_slots[sorted_slots[i][0]] = sorted_slots[i][1][0]

        return return_slots

    def check_voting_availability(self, voting_results):
        print(voting_results)
        participant_num = len(voting_results)
        proposed_start = self.proposed_meeting.time_slots[0]

        total_preference_dict = {}
        slot_list = voting_results[0].keys()

        for slot in slot_list:
            zero_preference = False
            total_preference = 0

            for i in range(participant_num):
                total_preference += voting_results[i][slot]

                if voting_results[i][slot] == 0:
                    zero_preference = True

            if not zero_preference:
                total_preference_dict[slot] = total_preference

        print(total_preference_dict)

        if len(total_preference_dict) == 0:
            return None
        elif len(total_preference_dict) == 1:
            return total_preference_dict[0]
        else:
            best_preference = 0
            best_distance = int(get_config('default', 'slot_division')) * participant_num
            best_slot = None

            for slot in total_preference_dict:
                cur_preference = 0

                for i in range(participant_num):
                    cur_preference += voting_results[i][slot]

                cur_distance = abs(slot - proposed_start)

                print(slot, cur_preference, cur_distance)

                if cur_preference > best_preference:
                    best_preference = cur_preference
                    best_distance = cur_distance
                    best_slot = slot
                elif cur_preference == best_preference and cur_distance < best_distance:
                    best_distance = cur_distance
                    best_slot = slot

            return best_slot





if __name__ == '__main__':
    host_agent = MeetingAgent('meeting-alice@404.city', 'meeting-alice')
    host_agent.start()

    guest_agent_1 = MeetingAgent('meeting-bob@404.city', 'meeting-bob')
    guest_agent_1.start()

    guest_agent_2 = MeetingAgent('meeting-calvin@404.city', 'meeting-calvin')
    guest_agent_2.start()
