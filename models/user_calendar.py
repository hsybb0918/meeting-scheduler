# @File        : user_calendar.py
# @Description :
# @Time        : 20 June, 2021
# @Author      : Cyan
import datetime
import json

from models.utils import get_config


class ScheduledMeeting:
    # meeting time
    month = None
    day = None
    year = None
    time_slots = None

    # meeting participants
    host_agent = None
    guest_agents = None

    # meeting information
    subject = ''
    location = ''
    description = ''

    def __init__(self, month, day, year):
        self.month = int(month)
        self.day = int(day)
        self.year = int(year)

    def set_time_slots(self, slot, *args):
        self.time_slots = []
        self.time_slots.append(int(slot))
        if args is not None:
            for value in args:
                self.time_slots.append(int(value))

    def set_time_slots_from_list(self, slot_list):
        self.time_slots = slot_list

    def set_participants(self, host, guest, *args):
        self.guest_agents = []
        self.host_agent = str(host)
        self.guest_agents.append(str(guest))
        if args is not None:
            for value in args:
                self.guest_agents.append(str(value))

    def set_host(self, host):
        self.host_agent = host

    def set_guests_from_list(self, guests_list):
        self.guest_agents = guests_list

    def set_information(self, subject, location='', description=''):
        self.subject = subject
        self.location = location
        self.description = description

    def __str__(self):
        date_str = str(self.month) + '-' + str(self.day) + '-' + str(self.year)
        slots_str = str(self.time_slots[0])
        guests_str = str(self.guest_agents[0])

        for value in self.time_slots[1:]:
            slots_str = slots_str + ', ' + str(value)
        for value in self.guest_agents[1:]:
            guests_str = guests_str + ', ' + str(value)

        return '[date: ' + date_str + '; time: ' + slots_str + \
               '; host: ' + self.host_agent + '; guests: ' + guests_str + \
               '; subject: ' + self.subject + '; location: ' + self.location + \
               '; description: ' + self.description + ']'

        # return 'date: ' + date_str + '\ntime: ' + slots_str + \
        #        '\nhost: ' + self.host_agent + '\nguests: ' + guests_str + \
        #        '\nsubject: ' + self.subject + '\nlocation: ' + self.location + '\ndescription: ' + self.description


class UserCalendar:
    scheduled_meetings = None
    global_slot_preference = None

    def __init__(self):
        self.scheduled_meetings = []
        self.global_slot_preference = {}

        self.init_global_slot_preference(int(get_config('default', 'slot_division')))

    def init_global_slot_preference(self, slot_num):
        for i in range(0, slot_num):
            self.global_slot_preference[i] = 5

    def check_time_slots(self, slots):
        for slot in slots:
            if self.global_slot_preference[slot] == 0:
                return False
        return True



if __name__ == '__main__':
    # c = UserCalendar()
    # for k, v in c.global_slot_preference.items():
    #     print(k, v)

    meeting = ScheduledMeeting(6, 30, 2021)
    meeting.set_time_slots(23, 24)
    meeting.set_participants('meeting-alice@404.city', 'meeting-bob@404.city', 'meeting-calvin@404.city')
    meeting.set_information('master thesis', 'ms team', 'talk about the project')

    print(meeting)

    d = json.dumps(meeting, default=lambda o: o.__dict__
                   # , sort_keys=True
                   # , indent=4
                   )
    o = json.loads(d)

    print(d)
    print(type(o), o)
    print(o.get('time_slots'))

    step = 0

    if step == 0:
        print(step)
        step = 1
        print(step)
    elif step == 1:
        print(step)
