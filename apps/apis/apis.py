# @File        : apis.py
# @Description :
# @Time        : 07 July, 2021
# @Author      : Cyan
import json
from time import sleep
from datetime import time, date, datetime

from flask import Blueprint
from flask_restful import Api, Resource, marshal_with, fields, reqparse, marshal

from apps import db
from apps.dbmodels.dbmodels import ScheduleModel, AgentModel, MeetingModel, OfficeModel, PreferenceModel
from models.meeting_agent import MeetingAgent
from models.user_calendar import OfficeTime, PreferenceTime, ScheduledMeeting, UserCalendar

bp = Blueprint('mams', __name__)
api = Api(bp)


class TimeFormat(fields.Raw):
    """
    field type for datetime.time
    """
    def format(self, value):
        return time.strftime(value, '%H:%M')


class DateFormat(fields.Raw):
    """
    field type for datetime.date
    """
    def format(self, value):
        return date.strftime(value, '%Y-%m-%d')


# fields for single agent
agent_fields = {
    'agent_id': fields.Integer,
    'email': fields.String,
    'password': fields.String
}

# fields for single meeting
meeting_fields = {
    'meeting_id': fields.Integer,
    'start_time': fields.DateTime,
    'end_time': fields.DateTime,
    'subject': fields.String,
    'location': fields.String,
    'description': fields.String
}

# fields for agent's meetings
agent_meetings_fields = {
    'agent_id': fields.Integer,
    'email': fields.String,
    'meetings': fields.List(fields.Nested(meeting_fields))
}

# fields for agent's offices
office_fields = {
    'start_time': TimeFormat,
    'end_time': TimeFormat
}

# fields for agent's preferences
preference_fields = {
    'start_time': TimeFormat,
    'end_time': TimeFormat,
    'priority': fields.Integer,
    'is_local': fields.Boolean,
    'specified_date': DateFormat
}

# parser for agent
agent_parser = reqparse.RequestParser()
agent_parser.add_argument('email', type=str, required=True, help='Email cannot be blank!')
agent_parser.add_argument('password', type=str, required=True, help='Password cannot be blank!')

# parser for meeting deletion
meeting_delete_parser = reqparse.RequestParser()
meeting_delete_parser.add_argument('agent_id', type=int)

# parser for office add
office_add_parser = reqparse.RequestParser()
office_add_parser.add_argument('start', type=str)
office_add_parser.add_argument('end', type=str)

# parser for preference add
preference_add_parser = reqparse.RequestParser()
preference_add_parser.add_argument('start', type=str)
preference_add_parser.add_argument('end', type=str)
preference_add_parser.add_argument('priority', type=int)
preference_add_parser.add_argument('local', type=str)
preference_add_parser.add_argument('date', type=str)

# parser for meeting request
meeting_request_parser = reqparse.RequestParser()
meeting_request_parser.add_argument('start', type=str)
meeting_request_parser.add_argument('end', type=str)
meeting_request_parser.add_argument('date', type=str)
meeting_request_parser.add_argument('subject', type=str)
meeting_request_parser.add_argument('location', type=str)
meeting_request_parser.add_argument('description', type=str)
meeting_request_parser.add_argument('host_id', type=str)
meeting_request_parser.add_argument('guests_id', type=str)


class AgentsResource(Resource):
    def get(self):
        """
        get all agents
        :return:
        """
        agents = AgentModel.query.all()
        data = marshal(agents, agent_fields)

        # agent_list = []
        #
        # for agent in agents:
        #     agent_single = marshal(agent, agent_fields)
        #     agent_list.append(agent_single)
        #
        # data = {
        #     'num': len(agents),
        #     'agents': agent_list
        # }

        return data

    def post(self):
        """
        add new agent
        :return:
        """
        args = agent_parser.parse_args()
        email = args.get('email')
        password = args.get('password')

        agent_query = AgentModel.query.filter(AgentModel.email == email).all()

        # agent already exists
        if len(agent_query) != 0:
            return {'code': 400, 'message': 'The agent already exists!'}

        # authenticate agent
        agent_test = MeetingAgent(email, password, None)
        try:
            agent_test.start().result()
        except:
            return {'code': 400, 'message': 'Could not authenticate the agent!'}
        else:
            agent_test.stop()
            db.session.add(AgentModel(email, password))
            db.session.commit()
            return {'code': 200, 'message': 'Agent has been created successfully!'}


class AgentResource(Resource):
    def get(self, aid):
        """
        get the agent with id
        :param aid:
        :return:
        """
        agent = AgentModel.query.get(aid)
        data = marshal(agent, agent_fields)

        return data

    def delete(self, aid):
        """
        delete the agent with id, can only delete agent without meeting
        :param aid:
        :return:
        """
        agent = AgentModel.query.get(aid)

        if len(agent.meetings) == 0:
            db.session.delete(agent)
            db.session.commit()
            return {'code': 200, 'message': 'Delete the agent successfully!'}
        else:
            return {'code': 400, 'message': 'You cannot delete the agent who has a meeting in the schedule!'}


class MeetingsResource(Resource):
    def get(self, aid):
        """
        get the meetings of the agent with id
        :param aid:
        :return:
        """
        agent = AgentModel.query.get(aid)

        # get all meeting ids
        mids = []
        for meeting in agent.meetings:
            mids.append(meeting.meeting_id)

        # get all meetings
        meetings = MeetingModel.query.filter(MeetingModel.meeting_id.in_(mids)).all()
        data_format = {
            'agent_id': agent.agent_id,
            'email': agent.email,
            'meetings': meetings
        }

        data = marshal(data_format, agent_meetings_fields)

        return data


class MeetingResource(Resource):
    def get(self, mid):
        """
        get the meeting with id
        :param mid:
        :return:
        """
        meeting = MeetingModel.query.get(mid)

        # marshal common fields
        data = marshal(meeting, meeting_fields)

        participants = []

        for agent in meeting.agents:
            participants.append(AgentModel.query.get(agent.agent_id).email)

        # add two string fields for display
        data['time_range'] = meeting.start_time.strftime('%m/%d/%Y %H:%M') + ' - ' + meeting.end_time.strftime('%H:%M')
        data['participants'] = participants

        return data

    def delete(self, mid):
        """
        delete the meeting with id, only host agent can delete meeting
        :param mid:
        :return:
        """
        args = meeting_delete_parser.parse_args()
        aid = args['agent_id']

        schedule = ScheduleModel.query.filter(ScheduleModel.agent_id == aid, ScheduleModel.meeting_id == mid).first()

        # check if the agent can cancel the meeting
        if schedule.is_host is True:
            ScheduleModel.query.filter(ScheduleModel.meeting_id == mid).delete()
            MeetingModel.query.filter(MeetingModel.meeting_id == mid).delete()
            db.session.commit()
            return {'code': 200, 'message': 'Cancel the meeting successfully!'}
        else:
            return {'code': 400, 'message': 'You cannot cancel the meeting that is not proposed by you!'}


class OfficesResource(Resource):
    def get(self, aid):
        """
        get offices for specific agent
        :param aid:
        :return:
        """
        offices = OfficeModel.query.filter(OfficeModel.agent_id == aid).all()
        data = marshal(offices, office_fields)
        return data

    def post(self, aid):
        """
        add office to specific agent
        :param aid:
        :return:
        """
        args = office_add_parser.parse_args()
        start = args.get('start')
        end = args.get('end')

        # parse time
        start_time = self.parse_time(start)
        end_time = self.parse_time(end)

        agent = AgentModel.query.get(aid)
        offices = agent.offices

        # time not valid
        if start_time >= end_time:
            return {'code': 400, 'message': 'The start time cannot exceed the end time!'}

        # time valid
        if len(offices) != 0:
            has_overlap = False
            for office in offices:
                if self.has_overlap(start_time, end_time, office.start_time, office.end_time):
                    has_overlap = True

            if has_overlap:
                return {'code': 400, 'message': 'Cannot intersect with the time that already exists!'}

        # add successfully
        om = OfficeModel(start_time, end_time)
        agent.offices.append(om)
        db.session.add(om)
        db.session.commit()
        return {'code': 200, 'message': 'Add the office time successfully!'}

    def parse_time(self, time_string):
        """
        parse string to time
        :param time_string:
        :return:
        """
        return time(int(time_string.split(':')[0]), int(time_string.split(':')[1]))

    def parse_date(self, date_string):
        """
        parse string to date
        :param date_string:
        :return:
        """
        return date(int(date_string.split('/')[2]), int(date_string.split('/')[0]), int(date_string.split('/')[1]))

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

        return latest_start < earliest_end


class OfficeResource(Resource):
    def get(self, oid):
        """
        get specific office according to id
        :param oid:
        :return:
        """
        office = OfficeModel.query.get(oid)
        data = marshal(office, office_fields)

        return data

    def delete(self, oid):
        """
        delete specific office according to id
        :param oid:
        :return:
        """
        office = OfficeModel.query.get(oid)
        try:
            db.session.delete(office)
            db.session.commit()
            return {'code': 200, 'message': 'Delete the office time successfully!'}
        except:
            return {'code': 400, 'message': 'Error occurred when deleting the office time!'}


class PreferencesResource(Resource):
    def get(self, aid):
        """
        get preferences for specific agent
        :param aid:
        :return:
        """
        preferences = PreferenceModel.query.filter(PreferenceModel.agent_id == aid).all()
        data = marshal(preferences, preference_fields)

        return data

    def post(self, aid):
        """
        add preference to specific agent
        :param aid:
        :return:
        """
        args = preference_add_parser.parse_args()
        start = args.get('start')
        end = args.get('end')
        priority = args.get('priority')
        local = args.get('local')
        date = args.get('date')

        is_local = False if local == 'false' else True

        # parse time
        start_time = self.parse_time(start)
        end_time = self.parse_time(end)

        specified_date = self.parse_date(date) if is_local else None

        agent = AgentModel.query.get(aid)
        preferences = agent.preferences

        # time not valid
        if start_time >= end_time:
            return {'code': 400, 'message': 'The start time cannot exceed the end time!'}

        # time valid
        if len(preferences) != 0:
            has_overlap = False

            if not is_local:
                for preference in preferences:
                    if not preference.is_local:
                        if self.has_overlap(start_time, end_time, preference.start_time, preference.end_time):
                            has_overlap = True

            if is_local:
                start_dt = datetime.combine(self.parse_date(date), self.parse_time(start))
                end_dt = datetime.combine(self.parse_date(date), self.parse_time(end))

                for preference in preferences:
                    if preference.is_local:
                        p_start_dt = datetime.combine(preference.specified_date, preference.start_time)
                        p_end_dt = datetime.combine(preference.specified_date, preference.end_time)

                        if self.has_overlap(start_dt, end_dt, p_start_dt, p_end_dt):
                            has_overlap = True

            if has_overlap:
                return {'code': 400, 'message': 'Cannot intersect with the time that already exists!'}

        # add successfully
        pm = PreferenceModel(start_time, end_time, priority, is_local, specified_date)
        agent.preferences.append(pm)
        db.session.add(pm)
        db.session.commit()
        return {'code': 200, 'message': 'Add the office time successfully!'}

    def parse_time(self, time_string):
        """
        parse string to time
        :param time_string:
        :return:
        """
        return time(int(time_string.split(':')[0]), int(time_string.split(':')[1]))

    def parse_date(self, date_string):
        """
        parse string to date
        :param date_string:
        :return:
        """
        return date(int(date_string.split('/')[2]), int(date_string.split('/')[0]), int(date_string.split('/')[1]))

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

        return latest_start < earliest_end


class PreferenceResource(Resource):
    def get(self, pid):
        """
        get specific preference according to id
        :param pid:
        :return:
        """
        preference = PreferenceModel.query.get(pid)
        data = marshal(preference, preference_fields)

        return data

    def delete(self, pid):
        """
        delete specific preference according to id
        :param pid:
        :return:
        """
        preference = PreferenceModel.query.get(pid)
        try:
            db.session.delete(preference)
            db.session.commit()
            return {'code': 200, 'message': 'Delete the preference successfully!'}
        except:
            return {'code': 400, 'message': 'Error occurred when deleting the preference!'}


class RequestMeetingResource(Resource):
    def post(self):
        """
        request the meeting
        :return:
        """
        args = meeting_request_parser.parse_args()
        start = args.get('start')
        end = args.get('end')
        date = args.get('date')
        subject = args.get('subject')
        location = args.get('location')
        description = args.get('description')
        host_id = args.get('host_id')
        guests_id = args.get('guests_id')

        # parse time
        start_time = datetime.combine(self.parse_date(date), self.parse_time(start))
        end_time = datetime.combine(self.parse_date(date), self.parse_time(end))

        # time not valid
        if start_time >= end_time:
            return {'code': 400, 'message': 'The start time cannot exceed the end time!'}

        # get the host agent model
        host = AgentModel.query.get(int(host_id))

        # get all meeting ids
        host_mids = []
        for meeting in host.meetings:
            host_mids.append(meeting.meeting_id)

        # get all meetings
        host_meetings = MeetingModel.query.filter(MeetingModel.meeting_id.in_(host_mids)).all()

        host_has_overlap = False
        for m in host_meetings:
            if self.has_overlap(m.start_time, m.end_time, start_time, end_time):
                host_has_overlap = True
        if host_has_overlap:
            return {'code': 300, 'message': 'You already have a meeting at this time!'}

        # get the guests agent model
        guests_id_list = []
        guests_email_list = []
        for guest in json.loads(guests_id):
            guests_id_list.append(int(guest))
            guests_email_list.append(AgentModel.query.get(int(guest)).email)
        guests = AgentModel.query.filter(AgentModel.agent_id.in_(guests_id_list)).all()

        all_agents = []

        # start guest agents
        for guest in guests:
            ma_guest = MeetingAgent(guest.email, guest.password, self.set_user_calendar(guest))
            ma_guest.start()
            all_agents.append(ma_guest)

        # start host agent
        ma_host = MeetingAgent(host.email, host.password, self.set_user_calendar(host))
        ma_host.start()
        all_agents.append(ma_host)

        # init the requested meeting
        sm = ScheduledMeeting(start_time, end_time, subject, location, description)
        sm.set_participants(host.email, guests_email_list)

        # wait for the agent start
        sleep(1)

        # propose the meeting
        ma_host.propose_meeting(sm)

        sleep(5)

        is_successful, meeting_success = ma_host.get_meeting_status()
        if is_successful:
            for agent in all_agents:
                agent.stop()

            # db operation
            meeting_add = MeetingModel(meeting_success.start_time, meeting_success.end_time, subject, location, description)
            schedules_add = []

            schedule_host = ScheduleModel(is_host=True)
            schedule_host.agent = host
            schedule_host.meeting = meeting_add
            schedules_add.append(schedule_host)

            for guest in guests:
                schedule_guest = ScheduleModel(is_host=False)
                schedule_guest.agent = guest
                schedule_guest.meeting = meeting_add
                schedules_add.append(schedule_guest)

            db.session.add(meeting_add)
            db.session.add_all(schedules_add)
            db.session.commit()

            return {'code': 200, 'message': 'Schedule the meeting successfully!'}
        elif not is_successful:
            for agent in all_agents:
                agent.stop()
            return {'code': 400, 'message': 'Failed to schedule the meeting!'}
        else:
            for agent in all_agents:
                agent.stop()
            return {'code': 400, 'message': 'Meeting negotiation timed out!'}

    def parse_time(self, time_string):
        """
        parse string to time
        :param time_string:
        :return:
        """
        return time(int(time_string.split(':')[0]), int(time_string.split(':')[1]))

    def parse_date(self, date_string):
        """
        parse string to date
        :param date_string:
        :return:
        """
        return date(int(date_string.split('/')[2]), int(date_string.split('/')[0]), int(date_string.split('/')[1]))

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

        return latest_start < earliest_end

    def set_user_calendar(self, agent_model):
        """
        database operation
        :param agent_model:
        :return:
        """
        schedules = []
        for meeting in agent_model.meetings:
            mm = MeetingModel.query.get(meeting.meeting_id)
            schedules.append(ScheduledMeeting(mm.start_time, mm.end_time, mm.subject, mm.location, mm.description))

        offices = []
        office_model = OfficeModel.query.filter(OfficeModel.agent_id == agent_model.agent_id).all()
        for office in office_model:
            offices.append(OfficeTime(office.start_time, office.end_time))

        preferences = []
        preference_model = PreferenceModel.query.filter(PreferenceModel.agent_id == agent_model.agent_id).all()
        for preference in preference_model:
            preferences.append(PreferenceTime(preference.start_time, preference.end_time, preference.priority
                                              , preference.is_local, preference.specified_date))

        return UserCalendar(schedules, offices, preferences)


api.add_resource(AgentsResource, '/api/agents')
api.add_resource(AgentResource, '/api/agent/<int:aid>')

api.add_resource(MeetingsResource, '/api/meetings/<int:aid>')
api.add_resource(MeetingResource, '/api/meeting/<int:mid>')

api.add_resource(OfficesResource, '/api/offices/<int:aid>')
api.add_resource(OfficeResource, '/api/office/<int:oid>')

api.add_resource(PreferencesResource, '/api/preferences/<int:aid>')
api.add_resource(PreferenceResource, '/api/preference/<int:pid>')

api.add_resource(RequestMeetingResource, '/api/request')
