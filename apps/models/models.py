# @File        : models.py
# @Description :
# @Time        : 07 July, 2021
# @Author      : Cyan
from apps import db


class ScheduleModel(db.Model):
    __tablename__ = 'schedule'

    agent_id = db.Column(db.Integer, db.ForeignKey('agent.agent_id'), primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.meeting_id'), primary_key=True)
    is_host = db.Column(db.Boolean, nullable=False)

    agent = db.relationship('AgentModel', back_populates='meetings')
    meeting = db.relationship('MeetingModel', back_populates='agents')


class AgentModel(db.Model):
    __tablename__ = 'agent'

    agent_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(120), nullable=False)

    offices = db.relationship('OfficeModel', backref='agent')
    preferences = db.relationship('PreferenceModel', backref='agent')

    meetings = db.relationship('ScheduleModel', back_populates='agent')

    def __init__(self, email, password):
        self.email = email
        self.password = password


class MeetingModel(db.Model):
    __tablename__ = 'meeting'

    meeting_id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    subject = db.Column(db.Text, nullable=False)
    location = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)

    agents = db.relationship('ScheduleModel', back_populates='meeting')

    def __init__(self, start_time, end_time, subject, location='', description=''):
        self.start_time = start_time
        self.end_time = end_time
        self.subject = subject
        self.location = location
        self.description = description


class OfficeModel(db.Model):
    __tablename__ = 'office'

    office_id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    agent_id = db.Column(db.Integer, db.ForeignKey('agent.agent_id'))

    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time


class PreferenceModel(db.Model):
    __tablename__ = 'preference'

    preference_id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    is_local = db.Column(db.Boolean, nullable=False)
    specified_date = db.Column(db.Date)

    agent_id = db.Column(db.Integer, db.ForeignKey('agent.agent_id'))

    def __init__(self, start_time, end_time, priority, is_local, specified_date=None):
        self.start_time = start_time
        self.end_time = end_time
        self.priority = priority
        self.is_local = is_local
        self.specified_date = specified_date
