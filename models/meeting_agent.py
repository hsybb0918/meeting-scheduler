# @File        : meeting_agent.py
# @Description :
# @Time        : 15 June, 2021
# @Author      : Cyan
import json
from datetime import datetime, time

from spade import agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

from models.user_calendar import ScheduledMeeting


class MeetingAgent(agent.Agent):
    user_calendar = None  # user calendar object

    proposed_meeting = None  # scheduled meeting object
    receivers = None  # list of jid string

    is_host = None  # boolean

    is_successful = None

    class ProposeRequest(CyclicBehaviour):
        """
        host behaviour class, propose request
        """
        async def on_start(self):
            print('{} -> propose request behaviour start'.format(self.agent.jid))

        async def run(self):
            # if the agent propose a meeting
            if self.agent.is_host:
                print('{} -> proposed meeting [{}]'.format(self.agent.jid, self.agent.proposed_meeting))

                # prepare data
                data = json.dumps({
                    'year': self.agent.proposed_meeting.get_year(),
                    'month': self.agent.proposed_meeting.get_month(),
                    'day': self.agent.proposed_meeting.get_day(),
                    'start_hour': self.agent.proposed_meeting.get_start_hour(),
                    'start_minute': self.agent.proposed_meeting.get_start_minute(),
                    'end_hour': self.agent.proposed_meeting.get_end_hour(),
                    'end_minute': self.agent.proposed_meeting.get_end_minute(),
                    'subject': self.agent.proposed_meeting.subject,
                    'location': self.agent.proposed_meeting.subject,
                    'description': self.agent.proposed_meeting.subject
                })

                # meeting_json = json.dumps(self.agent.proposed_meeting, default=lambda o: o.__dict__)
                # meeting_load = json.loads(meeting_json)
                # print('{} -> transferred message [{}]'.format(self.agent.jid, data))

                # prepare message
                request_msg = Message()
                request_msg.body = data
                request_msg.thread = 'simple-match'
                request_msg.set_metadata('performative', 'query')

                # send message to all guest agents
                for to in self.agent.receivers:
                    request_msg.to = to
                    await self.send(request_msg)
                    print('{} -> send the meeting request to {}'.format(self.agent.jid, to))

                self.agent.is_host = False

                # add next behavior
                self.agent.add_behaviour(self.agent.ProposeCounterproposal())
                # kill the behaviour
                self.kill()

        async def on_end(self):
            print('{} -> propose request behaviour end'.format(self.agent.jid))

    class ProposeCounterproposal(CyclicBehaviour):
        """
        host behaviour class, propose counterproposal
        """
        async def on_start(self):
            print('{} -> propose counterproposal behaviour start'.format(self.agent.jid))

        async def run(self):
            reply_msg_mt = Template()
            reply_msg_mt.thread = 'simple-match-reply'
            self.set_template(reply_msg_mt)

            # message reply count
            message_count = len(self.agent.receivers)
            agree_count = 0

            # receive all replies
            if self.mailbox_size() == message_count:
                # count agree number
                for i in range(message_count):
                    reply_msg_receive = await self.receive()

                    print('{} -> reply from {} [{}]'.format(self.agent.jid, reply_msg_receive.sender,
                                                            reply_msg_receive.get_metadata('performative')))

                    if reply_msg_receive.get_metadata('performative') == 'agree':
                        agree_count += 1

                # if not all agree, propose counterproposal
                if agree_count != message_count:
                    counterproposal_msg = Message()
                    counterproposal_msg.thread = 'counterproposal-process'
                    counterproposal_msg.set_metadata('performative', 'query')

                    for to in self.agent.receivers:
                        counterproposal_msg.to = to
                        await self.send(counterproposal_msg)
                        print('{} -> propose the counterproposal to {}'.format(self.agent.jid, to))

                    # add next behaviour
                    self.agent.add_behaviour(self.agent.ProposeVoting())

                # if all agree, send confirmation
                else:
                    success_msg = Message()
                    success_msg.thread = 'counterproposal-process'
                    success_msg.set_metadata('performative', 'inform')

                    for to in self.agent.receivers:
                        success_msg.to = to
                        await self.send(success_msg)
                        print('{} -> send the meeting confirmation to {}'.format(self.agent.jid, to))

                    # add the proposed meeting and clear the variables
                    self.agent.add_meeting(self.agent.proposed_meeting)
                    self.agent.receivers = None

                    # back to the first behaviour
                    self.agent.add_behaviour(self.agent.ProposeRequest())

                # kill this behaviour
                self.kill()

        async def on_end(self):
            print('{} -> propose counterproposal behaviour end'.format(self.agent.jid))

    class ProposeVoting(CyclicBehaviour):
        """
        host behaviour class, propose voting
        """
        async def on_start(self):
            print('{} -> propose voting behaviour start'.format(self.agent.jid))

        async def run(self):
            reply_msg_mt = Template()
            reply_msg_mt.thread = 'counterproposal-process-reply'
            self.set_template(reply_msg_mt)

            # message reply count
            message_count = len(self.agent.receivers)

            # receive all replies
            if self.mailbox_size() == message_count:
                counterproposals = []

                for i in range(message_count):
                    reply_msg_receive = await self.receive()

                    counterproposal = json.loads(reply_msg_receive.body)
                    counterproposals.append(counterproposal)

                    print('{} -> reply from {} [{}]'.format(self.agent.jid, reply_msg_receive.sender, counterproposal))

                self_choice = self.agent.find_counterproposal_slots(self.agent.proposed_meeting.start_time
                                                                    , self.agent.proposed_meeting.end_time)
                print('{} -> self choice [{}]'.format(self.agent.jid, self_choice))
                counterproposals.append(self_choice)

                best_slot = self.agent.check_counterproposal_availability(counterproposals)

                if best_slot is None:
                    # propose voting
                    print('{} -> cannot find the intersection time'.format(self.agent.jid))
                    print('{} -> propose the voting'.format(self.agent.jid))

                    voting_msg = Message()
                    voting_msg.thread = 'voting-process'
                    voting_msg.set_metadata('performative', 'query')

                    # prepare voting options
                    voting_choice = self.agent.find_voting_slots(self.agent.proposed_meeting.start_time
                                                                 , self.agent.proposed_meeting.end_time)

                    # print('{} -> voting choices with preference [{}]'.format(self.agent.jid, voting_choice))

                    voting_msg.body = json.dumps(list(voting_choice.keys()))
                    print('{} -> voting choices [{}]'.format(self.agent.jid, list(voting_choice.keys())))

                    for to in self.agent.receivers:
                        voting_msg.to = to
                        await self.send(voting_msg)
                        print('{} -> send the voting choices to {}'.format(self.agent.jid, to))

                    # add next behaviour
                    self.agent.add_behaviour(self.agent.ProposeConfirmation())

                else:
                    # success, confirm the meeting
                    print('{} -> find the intersection time at {}'.format(self.agent.jid, best_slot))

                    og_start = self.agent.proposed_meeting.start_time
                    og_end = self.agent.proposed_meeting.end_time

                    self.agent.proposed_meeting.start_time = best_slot
                    self.agent.proposed_meeting.end_time = og_end - og_start + best_slot

                    success_msg = Message()
                    success_msg.thread = 'voting-process'
                    success_msg.set_metadata('performative', 'inform')

                    data = json.dumps({
                        'year': self.agent.proposed_meeting.get_year(),
                        'month': self.agent.proposed_meeting.get_month(),
                        'day': self.agent.proposed_meeting.get_day(),
                        'start_hour': self.agent.proposed_meeting.get_start_hour(),
                        'start_minute': self.agent.proposed_meeting.get_start_minute(),
                        'end_hour': self.agent.proposed_meeting.get_end_hour(),
                        'end_minute': self.agent.proposed_meeting.get_end_minute()
                    })
                    success_msg.body = data

                    for to in self.agent.proposed_meeting.guest_agents:
                        success_msg.to = to
                        await self.send(success_msg)
                        print('{} -> send the meeting confirmation to {}'.format(self.agent.jid, to))

                    # add the proposed meeting and clear the variable
                    self.agent.add_meeting(self.agent.proposed_meeting)
                    self.agent.receivers = None

                    # back to the first behaviour
                    self.agent.add_behaviour(self.agent.ProposeRequest())

                # kill this behaviour
                self.kill()

        async def on_end(self):
            print('{} -> propose voting behaviour end'.format(self.agent.jid))

    class ProposeConfirmation(CyclicBehaviour):
        """
        host behaviour class, propose confirmation
        """
        async def on_start(self):
            print('{} -> propose confirmation behaviour start'.format(self.agent.jid))

        async def run(self):
            reply_msg_mt = Template()
            reply_msg_mt.thread = 'voting-process-reply'
            self.set_template(reply_msg_mt)

            # message reply count
            message_count = len(self.agent.receivers)

            # receive all replies
            if self.mailbox_size() == message_count:
                voting_results = []

                for i in range(message_count):
                    reply_msg_receive = await self.receive()

                    voting_result = json.loads(reply_msg_receive.body)
                    voting_results.append(voting_result)

                    print('{} -> reply from {} [{}]'.format(self.agent.jid, reply_msg_receive.sender, voting_result))

                self_voting = self.agent.find_voting_slots(self.agent.proposed_meeting.start_time
                                                           , self.agent.proposed_meeting.end_time)
                voting_results.append(self_voting)

                print('{} -> self voting [{}]'.format(self.agent.jid, self_voting))

                self.agent.check_voting_availability(voting_results)
                best_slot = self.agent.check_voting_availability(voting_results)

                final_msg = Message()
                final_msg.thread = 'final-process'

                if best_slot is None:
                    # failed to schedule the meeting
                    print('{} -> failed to schedule the meeting in the final process'.format(self.agent.jid))

                    final_msg.set_metadata('performative', 'failure')
                else:
                    # success, confirm the meeting
                    print('{} -> successfully schedule the meeting at {}'.format(self.agent.jid, best_slot))

                    og_start = self.agent.proposed_meeting.start_time
                    og_end = self.agent.proposed_meeting.end_time

                    self.agent.proposed_meeting.start_time = best_slot
                    self.agent.proposed_meeting.end_time = og_end - og_start + best_slot

                    data = json.dumps({
                        'year': self.agent.proposed_meeting.get_year(),
                        'month': self.agent.proposed_meeting.get_month(),
                        'day': self.agent.proposed_meeting.get_day(),
                        'start_hour': self.agent.proposed_meeting.get_start_hour(),
                        'start_minute': self.agent.proposed_meeting.get_start_minute(),
                        'end_hour': self.agent.proposed_meeting.get_end_hour(),
                        'end_minute': self.agent.proposed_meeting.get_end_minute()
                    })
                    final_msg.body = data

                    final_msg.set_metadata('performative', 'inform')

                    # add the proposed meeting
                    self.agent.add_meeting(self.agent.proposed_meeting)

                # send the final message
                for to in self.agent.receivers:
                    final_msg.to = to
                    await self.send(final_msg)
                    print('{} -> send the final decision to {}'.format(self.agent.jid, to))

                # clear the meeting variables
                self.agent.receivers = None

                # back to the first behaviour
                self.agent.add_behaviour(self.agent.ProposeRequest())

                # kill this behaviour
                self.kill()

        async def on_end(self):
            print('{} -> propose confirmation behaviour end'.format(self.agent.jid))

    class ResponseRequest(CyclicBehaviour):
        """
        guest behaviour class, response request
        """
        async def on_start(self):
            print('{} -> response request behaviour start'.format(self.agent.jid))

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
                data = json.loads(request_msg_receive.body)

                start_time = datetime(data['year'], data['month'], data['day'], data['start_hour'],
                                      data['start_minute'])
                end_time = datetime(data['year'], data['month'], data['day'], data['end_hour'], data['end_minute'])

                meeting = ScheduledMeeting(start_time, end_time, data['subject'], data['location'], data['description'])
                self.agent.proposed_meeting = meeting

                print('{} -> requested meeting [{}]'.format(self.agent.jid, self.agent.proposed_meeting))

                # prepare reply message
                request_msg_reply = Message()
                request_msg_reply.to = str(request_msg_receive.sender)
                request_msg_reply.thread = 'simple-match-reply'

                # check if the time is available
                if self.agent.check_time_availability(start_time, end_time):
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
            print('{} -> response request behaviour end'.format(self.agent.jid))

    class ResponseCounterproposal(CyclicBehaviour):
        """
        guest behaviour class, response counterproposal
        """
        async def on_start(self):
            print('{} -> response counterproposal behaviour start'.format(self.agent.jid))

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

                    counterproposal = json.dumps(
                        self.agent.find_counterproposal_slots(self.agent.proposed_meeting.start_time,
                                                              self.agent.proposed_meeting.end_time))
                    counterproposal_msg_reply.body = counterproposal

                    print('{} -> counterproposal [{}]'.format(self.agent.jid, counterproposal))

                    # send the reply message
                    await self.send(counterproposal_msg_reply)

                    # add response voting behaviour
                    self.agent.add_behaviour(self.agent.ResponseVoting())

                elif counterproposal_metadata == 'inform':
                    # success
                    print('{} -> receive the meeting confirmation from {} to {}'.format(self.agent.jid
                                                                                        , self.agent.proposed_meeting.start_time
                                                                                        , self.agent.proposed_meeting.end_time))

                    # add the proposed meeting and clear the variable
                    self.agent.add_meeting(self.agent.proposed_meeting)
                    self.agent.receivers = None

                    # back to the first behaviour
                    self.agent.add_behaviour(self.agent.ResponseRequest())

                self.kill()

        async def on_end(self):
            print('{} -> response counterproposal behaviour end'.format(self.agent.jid))

    class ResponseVoting(CyclicBehaviour):
        """
        guest behaviour class, response voting
        """
        async def on_start(self):
            print('{} -> response voting behaviour start'.format(self.agent.jid))

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
                    voting_choice = json.loads(voting_msg_receive.body)
                    print('{} -> receive voting request for [{}]'.format(self.agent.jid, voting_choice))

                    voting_result = self.agent.voting_for_choices(voting_choice
                                                                  , self.agent.proposed_meeting.start_time.date()
                                                                  , self.agent.proposed_meeting.end_time - self.agent.proposed_meeting.start_time)

                    # prepare reply message
                    voting_msg_reply = Message()
                    voting_msg_reply.to = str(voting_msg_receive.sender)
                    voting_msg_reply.thread = 'voting-process-reply'

                    voting_msg_reply.body = json.dumps(voting_result)

                    print('{} -> voting result [{}]'.format(self.agent.jid, json.dumps(voting_result)))

                    # send the reply message
                    await self.send(voting_msg_reply)

                    # add next behaviour
                    self.agent.add_behaviour(self.agent.ResponseConfirmation())

                elif voting_metadata == 'inform':
                    # success
                    # change the meeting time
                    data = json.loads(voting_msg_receive.body)

                    start_time = datetime(data['year'], data['month'], data['day'], data['start_hour'],
                                          data['start_minute'])
                    end_time = datetime(data['year'], data['month'], data['day'], data['end_hour'], data['end_minute'])

                    self.agent.proposed_meeting.start_time = start_time
                    self.agent.proposed_meeting.end_time = end_time

                    print('{} -> receive the meeting confirmation from {} to {}'.format(self.agent.jid
                                                                                        , self.agent.proposed_meeting.start_time
                                                                                        , self.agent.proposed_meeting.end_time))

                    # add the proposed meeting and clear the variable
                    self.agent.add_meeting(self.agent.proposed_meeting)
                    self.agent.receivers = None

                    # back to the first behaviour
                    self.agent.add_behaviour(self.agent.ResponseRequest())

                self.kill()

        async def on_end(self):
            print('{} -> response voting behaviour end'.format(self.agent.jid))

    class ResponseConfirmation(CyclicBehaviour):
        """
        guest behaviour class, response confirmation
        """
        async def on_start(self):
            print('{} -> response confirmation behaviour start'.format(self.agent.jid))

        async def run(self):
            final_msg_mt = Template()
            final_msg_mt.thread = 'final-process'
            self.set_template(final_msg_mt)

            # receive the final message
            if self.mailbox_size() == 1:
                final_msg_receive = await self.receive()

                decision = final_msg_receive.get_metadata('performative')

                if decision == 'failure':
                    print('{} -> failed to schedule the meeting'.format(self.agent.jid))
                elif decision == 'inform':
                    # change the meeting time
                    data = json.loads(final_msg_receive.body)

                    start_time = datetime(data['year'], data['month'], data['day'], data['start_hour'],
                                          data['start_minute'])
                    end_time = datetime(data['year'], data['month'], data['day'], data['end_hour'], data['end_minute'])

                    self.agent.proposed_meeting.start_time = start_time
                    self.agent.proposed_meeting.end_time = end_time

                    print('{} -> schedule the meeting successfully'.format(self.agent.jid))

                    # add the proposed meeting
                    self.agent.add_meeting(self.agent.proposed_meeting)

                # clear the meeting variables
                self.agent.receivers = None

                # back to the first behaviour
                self.agent.add_behaviour(self.agent.ResponseRequest())
                # kill the current behaviour
                self.kill()

        async def on_end(self):
            print('{} -> response confirmation behaviour end'.format(self.agent.jid))

    def __init__(self, jid, password, user_calendar):
        super().__init__(jid, password)

        self.user_calendar = user_calendar
        self.is_host = False
        self.is_successful = False

    async def setup(self):
        """
        setup the agent when the agent start
        :return:
        """
        # start the agent
        print('{} -> start'.format(str(self.jid)))

        # add two types of behaviours, initial behaviours
        self.add_behaviour(self.ProposeRequest())
        self.add_behaviour(self.ResponseRequest())

    def propose_meeting(self, meeting):
        """
        agent proposes a meeting and set self as host
        :param meeting:
        :return:
        """
        self.proposed_meeting = meeting
        self.receivers = meeting.guest_agents
        self.is_host = True

    def add_meeting(self, meeting):
        """
        add meeting if negotiation successful
        :param meeting:
        :return:
        """
        self.user_calendar.add_meeting(meeting)
        self.is_successful = True

        # todo: database insert, not here

        print('{} -> schedule the meeting successfully'.format(self.jid))
        print('{} -> now the number of meetings is {}'.format(self.jid, len(self.user_calendar.schedules)))

    def check_time_availability(self, start, end):
        """
        check time availability for schedules, offices and preferences
        :param start:
        :param end:
        :return:
        """
        if self.user_calendar.has_conflict_schedules(start, end):
            print('{} -> conflict schedules'.format(self.jid))
            return False
        if self.user_calendar.has_conflict_offices(start, end):
            print('{} -> conflict offices'.format(self.jid))
            return False
        if self.user_calendar.has_conflict_preferences(start, end):
            print('{} -> conflict preferences'.format(self.jid))
            return False

        return True

    def find_counterproposal_slots(self, start, end):
        """
        find 5 time slots for counterproposal
        :param start:
        :param end:
        :return:
        """
        return self.user_calendar.find_free_slots(start, end, 5)

    def find_voting_slots(self, start, end):
        """
        find 10 time slots for voting
        :param start:
        :param end:
        :return:
        """
        return self.user_calendar.find_free_slots(start, end, 10)

        # available_slots = {}
        #
        # proposed_start = self.proposed_meeting.time_slots[0]
        # slot_num = len(self.proposed_meeting.time_slots)
        # for start in range(48 - slot_num + 1):
        #     is_available = True
        #     preference_total = 0
        #     for i in range(slot_num):
        #         preference_total += self.user_calendar.global_slot_preference[start + i]
        #
        #         if self.user_calendar.global_slot_preference[start + i] == 0:
        #             is_available = False
        #
        #     if is_available:
        #         preference_avg = round(preference_total / slot_num, 1)
        #         distance = abs(start - proposed_start)
        #         counter_distance = 48 - distance
        #
        #         available_slots[start] = [preference_avg, counter_distance]
        #
        # # sort and choose 10 slot range
        # return_slots = {}
        #
        # sorted_slots = sorted(available_slots.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True)
        # for i in range(10):
        #     return_slots[sorted_slots[i][0]] = sorted_slots[i][1][0]
        #
        # return return_slots

    def voting_for_choices(self, choices, date, duration):
        """
        guest agents vote for received choices
        :param choices:
        :param date:
        :param duration:
        :return:
        """
        voting_result = {}

        for choice in choices:
            meeting_time = time(int(choice.split(':')[0]), int(choice.split(':')[1]))
            dt_start = datetime.combine(date, meeting_time)
            dt_end = dt_start + duration

            choice_preference = self.user_calendar.compute_total_preference(dt_start, dt_end)
            # print(dt_start, dt_end, choice_preference)

            voting_result[choice] = choice_preference

        return voting_result

    def check_counterproposal_availability(self, counters):
        """
        check the availability of received counterproposal
        :param counters:
        :return:
        """
        counter_list = []
        for counter in counters:
            counter_list.append(list(counter.keys()))

        counter_intersection = list(set.intersection(*map(set, counter_list)))
        # print(counter_intersection)

        if len(counter_intersection) == 0:
            return None
        else:
            m_dt = self.proposed_meeting.start_time

            best_p = 0
            best_d = None
            best_c = None

            for c in counter_intersection:
                total_p = 0
                for i in range(len(counters)):
                    total_p += counters[i][c]

                c_dt = datetime.combine(m_dt.date(), time(int(c.split(':')[0]), int(c.split(':')[1])))

                if total_p > best_p:
                    best_p = total_p
                    best_d = abs(m_dt - c_dt)
                    best_c = c_dt
                elif total_p == best_p:
                    if abs(m_dt - c_dt) < best_d:
                        best_d = abs(m_dt - c_dt)
                        best_c = c_dt

            return best_c

    def check_voting_availability(self, voting_results):
        """
        check availability of vote choices
        :param voting_results:
        :return:
        """
        keys = list(voting_results[0].keys())

        available_voting = {}

        for key in keys:
            total_preference = 0
            has_zero = False
            for voting in voting_results:
                if voting[key] == 0:
                    has_zero = True
                else:
                    total_preference += voting[key]
            if not has_zero:
                available_voting[key] = total_preference

        # print(voting_results, '\n', available_voting)

        # sort available_voting
        if len(available_voting) == 0:
            return None
        else:
            best_p = 0  # best preference
            best_d = None  # best distance
            best_v = None  # best voting key

            for k, v in available_voting.items():
                voting_dt = datetime.combine(self.proposed_meeting.start_time.date(),
                                             time(int(k.split(':')[0]), int(k.split(':')[1])))

                if v > best_p:
                    best_p = v
                    best_d = abs(self.proposed_meeting.start_time - voting_dt)
                    best_v = voting_dt
                elif v == best_p:
                    if abs(self.proposed_meeting.start_time - voting_dt) < best_d:
                        best_d = abs(self.proposed_meeting.start_time - voting_dt)
                        best_v = voting_dt

            # print('best voting time', best_v)

            return best_v

        # participant_num = len(voting_results)
        # proposed_start = self.proposed_meeting.time_slots[0]
        #
        # total_preference_dict = {}
        # slot_list = voting_results[0].keys()
        #
        # for slot in slot_list:
        #     zero_preference = False
        #     total_preference = 0
        #
        #     for i in range(participant_num):
        #         total_preference += voting_results[i][slot]
        #
        #         if voting_results[i][slot] == 0:
        #             zero_preference = True
        #
        #     if not zero_preference:
        #         total_preference_dict[slot] = total_preference
        #
        # print(total_preference_dict)
        #
        # if len(total_preference_dict) == 0:
        #     return None
        # elif len(total_preference_dict) == 1:
        #     return total_preference_dict[0]
        # else:
        #     best_preference = 0
        #     best_distance = 48 * participant_num
        #     best_slot = None
        #
        #     for slot in total_preference_dict:
        #         cur_preference = 0
        #
        #         for i in range(participant_num):
        #             cur_preference += voting_results[i][slot]
        #
        #         cur_distance = abs(slot - proposed_start)
        #
        #         print(slot, cur_preference, cur_distance)
        #
        #         if cur_preference > best_preference:
        #             best_preference = cur_preference
        #             best_distance = cur_distance
        #             best_slot = slot
        #         elif cur_preference == best_preference and cur_distance < best_distance:
        #             best_distance = cur_distance
        #             best_slot = slot
        #
        #     return best_slot

    def get_meeting_status(self):
        meeting = self.proposed_meeting
        self.proposed_meeting = None
        return self.is_successful, meeting


if __name__ == '__main__':
    pass
