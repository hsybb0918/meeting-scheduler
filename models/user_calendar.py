# @File        : user_calendar.py
# @Description :
# @Time        : 20 June, 2021
# @Author      : Cyan
import datetime

from models.utils import get_config


class ScheduledMeeting:
    slots = []
    participants = []
    subject = ""
    location = ""
    description = ""

    def __init__(self, slots, participants, subject, location="", description=""):
        self.slots = slots
        self.participants = participants
        self.subject = subject
        self.location = location
        self.description = description


class ScheduledDay:
    date = None
    unavailable_slots = []
    meetings = []

    def __init__(self, year, month, day):
        self.date = datetime.date(year, month, day)


class UserCalendar:
    scheduled_days = []
    global_slot_preference = {}
    global_weekday_preference = {}

    def __init__(self):
        self.init_global_slot_preference(int(get_config("default", "slot_division")))
        self.init_global_weekday_preference()

    def init_global_slot_preference(self, slot_num):
        for i in range(0, slot_num):
            self.global_slot_preference[i] = 5

    def init_global_weekday_preference(self):
        for i in range(0, 7):
            self.global_weekday_preference[i] = 5


if __name__ == '__main__':
    c = UserCalendar()
    for k, v in c.global_slot_preference.items():
        print(k, v)
    for k, v in c.global_weekday_preference.items():
        print(k, v)
