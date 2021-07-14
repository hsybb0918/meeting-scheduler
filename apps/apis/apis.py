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
from apps.models.models import ScheduleModel, AgentModel, MeetingModel, OfficeModel, PreferenceModel
from models.meeting_agent import MeetingAgent
from models.user_calendar import OfficeTime, PreferenceTime, ScheduledMeeting, UserCalendar

bp = Blueprint('mams', __name__)
api = Api(bp)

# for single agent
agent_fields = {
    'agent_id': fields.Integer,
    'email': fields.String,
    'password': fields.String
}

# for single meeting
meeting_fields = {
    'meeting_id': fields.Integer,
    'start_time': fields.DateTime,
    'end_time': fields.DateTime,
    'subject': fields.String,
    'location': fields.String,
    'description': fields.String
}

# for agent's meetings
agent_meetings_fields = {
    'agent_id': fields.Integer,
    'email': fields.String,
    'meetings': fields.List(fields.Nested(meeting_fields))
}

# agent parser
agent_parser = reqparse.RequestParser()
agent_parser.add_argument('email', type=str, required=True, help='Email cannot be blank!')
agent_parser.add_argument('password', type=str, required=True, help='Password cannot be blank!')

# delete meeting parser
meeting_delete_parser = reqparse.RequestParser()
meeting_delete_parser.add_argument('agent_id', type=int)

# meeting request parser
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
        get all agents with id, name and email, no password returned
        :return:
        """
        agents = AgentModel.query.all()

        agent_list = []

        for agent in agents:
            agent_single = {
                'agent_id': agent.agent_id,
                'name': agent.email.split('@')[0],
                'email': agent.email
            }
            agent_list.append(agent_single)

        data = {
            'num': len(agents),
            'agents': agent_list
        }

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
            return {'code': 300, 'message': 'The agent already exists!'}

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
    @marshal_with(agent_fields)
    def get(self, aid):
        """
        get the agent with id
        :param aid:
        :return:
        """
        agent = AgentModel.query.get(aid)
        return agent


class MeetingsResource(Resource):
    @marshal_with(agent_meetings_fields)
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
        data = {
            'agent_id': agent.agent_id,
            'email': agent.email,
            'meetings': meetings
        }

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

        # add two fields
        data['time_range'] = meeting.start_time.strftime('%m/%d/%Y %H:%M') + ' - ' + meeting.end_time.strftime('%H:%M')
        data['participants'] = participants

        return data

    def delete(self, mid):
        """
        delete the meeting with id
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

        # get the host agent model
        host = AgentModel.query.get(int(host_id))

        # get the guests agent model
        guests_id_list = []
        guests_email_list = []
        for guest in json.loads(guests_id):
            guests_id_list.append(int(guest))
            guests_email_list.append(AgentModel.query.get(int(guest)).email)
        guests = AgentModel.query.filter(AgentModel.agent_id.in_(guests_id_list)).all()

        # start guest agents
        for guest in guests:
            ma_guest = MeetingAgent(guest.email, guest.password, self.set_user_calendar(guest))
            ma_guest.start()

        # start host agent
        ma_host = MeetingAgent(host.email, host.password, self.set_user_calendar(host))
        ma_host.start()

        # init the requested meeting
        sm = ScheduledMeeting(start_time, end_time, subject, location, description)
        sm.set_participants(host.email, guests_email_list)

        # wait for the agent start
        sleep(1)

        # propose the meeting
        ma_host.propose_meeting(sm)

        return {'code': 200}

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

    def set_user_calendar(self, agent_model):
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
api.add_resource(RequestMeetingResource, '/api/request')
