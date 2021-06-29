# @File        : user_calendar.py
# @Description :
# @Time        : 20 June, 2021
# @Author      : Cyan
import datetime
import json

from models.utils import get_config


class ScheduledMeeting:
    # meeting time
    date = None
    time_slots = None

    # meeting participants
    host_agent = ''
    guest_agents = None

    # meeting information
    subject = ''
    location = ''
    description = ''

    def __init__(self, subject, location='', description=''):
        self.subject = subject
        self.location = location
        self.description = description

    def set_date(self, year, month, day):
        self.date = datetime.date(year, month, day)

    def set_time_slots(self, slot, *args):
        self.time_slots = []
        self.time_slots.append(int(slot))
        if args is not None:
            for value in args:
                self.time_slots.append(int(value))

    def set_participants(self, host, guest, *args):
        self.guest_agents = []
        self.host_agent = str(host)
        self.guest_agents.append(str(guest))
        if args is not None:
            for value in args:
                self.guest_agents.append(str(value))

    def __str__(self):
        slots_str = str(self.time_slots[0])
        guests_str = str(self.guest_agents[0])

        for value in self.time_slots[1:]:
            slots_str = slots_str + ', ' + str(value)
        for value in self.guest_agents[1:]:
            guests_str = guests_str + ', ' + str(value)

        return '{date: ' + self.date.isoformat() + '; time: ' + slots_str + '; host: ' + \
               self.host_agent + '; guests: ' + guests_str + \
               '; subject: ' + self.subject + '; location: ' + self.location + \
               '; description: ' + self.description + '}'


class ScheduledDay:
    date = None
    scheduled_meetings = []

    def __init__(self, year, month, day):
        self.date = datetime.date(year, month, day)

    def add_meeting(self, meeting):
        self.scheduled_meetings.append(meeting)


class UserCalendar:
    scheduled_days = []
    global_slot_preference = {}

    def __init__(self):
        self.init_global_slot_preference(int(get_config('default', 'slot_division')))

    def init_global_slot_preference(self, slot_num):
        for i in range(0, slot_num):
            self.global_slot_preference[i] = 5


if __name__ == '__main__':
    c = UserCalendar()
    for k, v in c.global_slot_preference.items():
        print(k, v)

    print(json.dumps(c))
