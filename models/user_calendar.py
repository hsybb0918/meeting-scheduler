# @File        : user_calendar.py
# @Description :
# @Time        : 20 June, 2021
# @Author      : Cyan
from datetime import datetime, time, timedelta
import json


class UserCalendar:
    schedules = None
    offices = None
    preferences = None

    def __init__(self, schedules, offices, preferences):
        self.schedules = schedules
        self.offices = offices
        self.preferences = preferences

    def has_conflict_schedules(self, start, end):
        for meeting in self.schedules:
            # conflict
            if self.has_overlap(start, end, meeting.start_time, meeting.end_time):
                return True
        return False

    def has_conflict_offices(self, start, end):
        start_t = start.time()
        end_t = end.time()

        num_conflict = 0

        for office in self.offices:
            # conflict
            if not (office.start_time <= start_t <= office.end_time) or not (
                    office.start_time <= end_t <= office.end_time):
                num_conflict += 1

        return True if num_conflict == len(self.offices) else False

    def has_conflict_preferences(self, start, end):
        start_t = start.time()
        end_t = end.time()

        for preference in self.preferences:
            if preference.is_local:  # local preference
                p_start = datetime.combine(preference.specified_date, preference.start_time)
                p_end = datetime.combine(preference.specified_date, preference.end_time)

                if self.has_overlap(start, end, p_start, p_end):
                    if preference.priority == 0:
                        return True
            else:  # global preference
                if self.has_overlap(start_t, end_t, preference.start_time, preference.end_time):
                    if preference.priority == 0:
                        return True
            return False

    def find_free_slots(self, start, end, num):
        m_date = start.date()

        # find all meetings and unavailable office time
        day_unavailable = []
        for meeting in self.schedules:
            if meeting.start_time.date() == m_date:
                day_unavailable.append((meeting.start_time, meeting.end_time))

        for i in range(len(self.offices) - 1):
            start_dt = datetime.combine(m_date, self.offices[i].end_time)
            end_dt = datetime.combine(m_date, self.offices[i + 1].start_time)
            day_unavailable.append((start_dt, end_dt))

        # find day start and end
        day_start = datetime.combine(m_date, time(0, 0))
        day_end = datetime.combine(m_date, time(23, 30))

        # todo: offices need sorted
        if len(self.offices) != 0:
            day_start = datetime.combine(m_date, self.offices[0].start_time)
            day_end = datetime.combine(m_date, self.offices[-1].end_time)

        # duration
        duration = end - start

        # find available slots
        day_available = []

        slots = sorted([(day_start, day_start)] + day_unavailable + [(day_end, day_end)])
        for ss, ee in ((slots[i][1], slots[i + 1][0]) for i in range(len(slots) - 1)):
            # assert start <= end, "cannot attend all appointments"
            while ss + duration <= ee:
                day_available.append((ss, ss + duration))
                ss += timedelta(minutes=30)

        # set preference and negative distance
        slots_available = {}
        for ss, ee in day_available:
            slot_p = self.compute_total_preference(ss, ee)
            if slot_p != 0:
                slots_available[ss] = [slot_p, - abs(ss - start)]
            print(ss, 'preference', self.compute_total_preference(ss, ee))

        sorted_slots = sorted(slots_available.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True)

        returned_slots = {}
        for i in range(num):
            if i < len(sorted_slots):
                key = '{:%H:%M}'.format(sorted_slots[i][0])
                returned_slots[key] = sorted_slots[i][1][0]

        return returned_slots

    def compute_total_preference(self, start, end):
        total_preference = 0
        is_unavailable = False

        start_point = start
        while start_point < end:
            find_preference = False
            for preference in self.preferences:
                if find_preference:
                    break
                else:
                    p_start = datetime.combine(start.date(), preference.start_time)
                    p_end = datetime.combine(start.date(), preference.end_time)
                    if (preference.is_local and preference.specified_date == start.date()) or (not preference.is_local):
                        if p_start <= start_point < p_end:
                            find_preference = True
                            if preference.priority == 0:
                                is_unavailable = True
                            else:
                                total_preference += preference.priority
            if not find_preference:
                total_preference += 5

            start_point += timedelta(minutes=30)

        return 0 if is_unavailable else total_preference

    def add_meeting(self, meeting):
        self.schedules.append(meeting)

    def has_overlap(self, a_start, a_end, b_start, b_end):
        """
        if two time slots have overlap
        :param a_start:
        :param a_end:
        :param b_start:
        :param b_end:
        :return:
        """
        latest_start = max(a_start, b_start)
        earliest_end = min(a_end, b_end)

        return latest_start <= earliest_end

    def __str__(self):
        schedule_list = []
        for schedule in self.schedules:
            schedule_list.append(str(schedule))

        office_list = []
        for office in self.offices:
            office_list.append(str(office))

        preference_list = []
        for preference in self.preferences:
            preference_list.append(str(preference))

        return 'Schedules: {}\nOffices: {}\nPreferences: {}'\
            .format(schedule_list, office_list, preference_list)


class ScheduledMeeting:
    start_time = None  # datetime
    end_time = None  # datetime

    subject = None  # string
    location = None  # string
    description = None  # string

    host_agent = None  # string
    guest_agents = None  # list of string

    def __init__(self, start_time, end_time, subject, location, description=''):
        self.start_time = start_time
        self.end_time = end_time
        self.subject = subject
        self.location = location
        self.description = description

    def set_participants(self, host_agent, guest_agents):
        """
        set host agent and guest agents
        :param host_agent:
        :param guest_agents:
        :return:
        """
        self.host_agent = host_agent
        self.guest_agents = guest_agents

    def get_year(self):
        """
        get the year of meeting
        :return:
        """
        return self.start_time.year

    def get_month(self):
        """
        get the month of meeting
        :return:
        """
        return self.start_time.month

    def get_day(self):
        """
        get the day of meeting
        :return:
        """
        return self.start_time.day

    def get_start_hour(self):
        """
        get the start hour of the meeting
        :return:
        """
        return self.start_time.hour

    def get_start_minute(self):
        """
        get the start minute of the meeting
        :return:
        """
        return self.start_time.minute

    def get_end_hour(self):
        """
        get the end hour of the meeting
        :return:
        """
        return self.end_time.hour

    def get_end_minute(self):
        """
        get the end minute of the meeting
        :return:
        """
        return self.end_time.minute

    def __str__(self):
        return 'Meeting: start({}), end({}), subject({}), location({}), description({})'\
            .format(self.start_time, self.end_time, self.subject, self.location, self.description)


class OfficeTime:
    start_time = None  # time
    end_time = None  # time

    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return 'Office: start({}), end({})'.format(self.start_time, self.end_time)


class PreferenceTime:
    start_time = None  # time
    end_time = None  # time
    priority = None  # integer from 0 to 10
    is_local = None  # boolean
    specified_date = None  # date

    def __init__(self, start_time, end_time, priority, is_local, specified_date=None):
        self.start_time = start_time
        self.end_time = end_time
        self.priority = priority
        self.is_local = is_local
        self.specified_date = specified_date

    def __str__(self):
        if self.is_local:
            return 'Preference: start({}), end({}), priority({}), specified_date({})'.format(self.start_time
                                                                                             , self.end_time
                                                                                             , self.priority
                                                                                             , self.specified_date)
        else:
            return 'Preference: start({}), end({}), priority({})'.format(self.start_time, self.end_time, self.priority)
