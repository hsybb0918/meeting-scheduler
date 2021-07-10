# @File        : apis.py
# @Description :
# @Time        : 07 July, 2021
# @Author      : Cyan
from flask import Blueprint
from flask_restful import Api, Resource, marshal_with, fields, reqparse, marshal
from spade.agent import Agent

from apps import db
from apps.models.models import ScheduleModel, AgentModel, MeetingModel, OfficeModel, PreferenceModel

bp = Blueprint('mams', __name__)
api = Api(bp)

agent_fields = {
    'agent_id': fields.Integer,
    'email': fields.String,
    'password': fields.String
}

meeting_fields = {
    'meeting_id': fields.Integer,
    'start_time': fields.DateTime,
    'end_time': fields.DateTime,
    'subject': fields.String,
    'location': fields.String,
    'description': fields.String
}

agent_meetings_fields = {
    'agent_id': fields.Integer,
    'email': fields.String,
    'meetings': fields.List(fields.Nested(meeting_fields))
}

# request parsing
parser = reqparse.RequestParser()
parser.add_argument('email', type=str, required=True, help='Name cannot be blank!')
parser.add_argument('password', type=str, required=True, help='Name cannot be blank!')



class AgentsResource(Resource):
    @marshal_with(agent_fields)
    def get(self):

        agents = AgentModel.query.all()
        return agents

    def post(self):
        args = parser.parse_args()
        email = args.get('email')
        password = args.get('password')
        Agent
        return {'email': email, 'password': password}

    # def put(self):
    #     args = parser.parse_args()

class AgentResource(Resource):
    @marshal_with(agent_fields)
    def get(self, aid):
        agent = AgentModel.query.get(aid)
        return agent

class MeetingsResource(Resource):
    @marshal_with(agent_meetings_fields)
    def get(self, aid):
        agent = AgentModel.query.get(aid)
        mids = []
        for meeting in agent.meetings:
            mids.append(meeting.meeting_id)

        meetings = MeetingModel.query.filter(MeetingModel.meeting_id.in_(mids)).all()
        data = {
            'agent_id': agent.agent_id,
            'email': agent.email,
            # 'meetings': marshal(meetings, meeting_fields),
            'meetings': meetings
        }

        return data



api.add_resource(AgentsResource, '/agents')
api.add_resource(AgentResource, '/agent/<int:aid>')
api.add_resource(MeetingsResource, '/meetings/<int:aid>')
