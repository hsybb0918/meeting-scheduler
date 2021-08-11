from datetime import datetime, time, date

from flask import render_template

from apps import create_app, db
from apps.dbmodels.dbmodels import ScheduleModel, AgentModel, MeetingModel, OfficeModel, PreferenceModel

app = create_app()


@app.route('/', methods=['GET'])
def index():
    # # create database dbmodels
    # db.create_all()

    # # initial settings
    # agent1 = AgentModel('meeting-alice@404.city', 'meeting-alice')
    # agent2 = AgentModel('meeting-bob@404.city', 'meeting-bob')
    # agent3 = AgentModel('meeting-calvin@404.city', 'meeting-calvin')
    # agent4 = AgentModel('meeting-david@404.city', 'meeting-david')
    # agent5 = AgentModel('meeting-emma@404.city', 'meeting-emma')
    #
    # meeting1 = MeetingModel(datetime(2021, 7, 28, 11, 0), datetime(2021, 7, 28, 12, 0)
    #                         , 'Calendar project', 'Team', 'Talk about the progress of the project')
    # meeting2 = MeetingModel(datetime(2021, 8, 8, 14, 0), datetime(2021, 8, 8, 16, 0)
    #                         , 'Go to the movie', 'VUE', 'Tenet')
    # meeting3 = MeetingModel(datetime(2021, 8, 18, 9, 0), datetime(2021, 8, 18, 10, 0)
    #                         , 'Job interview', 'Zoom', 'The third interview')
    #
    # schedule1 = ScheduleModel(is_host=True)
    # schedule1.agent = agent1
    # schedule1.meeting = meeting1
    # schedule2 = ScheduleModel(is_host=False)
    # schedule2.agent = agent2
    # schedule2.meeting = meeting1
    # schedule3 = ScheduleModel(is_host=False)
    # schedule3.agent = agent3
    # schedule3.meeting = meeting1
    #
    # schedule5 = ScheduleModel(is_host=False)
    # schedule5.agent = agent1
    # schedule5.meeting = meeting2
    # schedule4 = ScheduleModel(is_host=True)
    # schedule4.agent = agent2
    # schedule4.meeting = meeting2
    #
    # schedule8 = ScheduleModel(is_host=False)
    # schedule8.agent = agent3
    # schedule8.meeting = meeting3
    # schedule7 = ScheduleModel(is_host=False)
    # schedule7.agent = agent4
    # schedule7.meeting = meeting3
    # schedule6 = ScheduleModel(is_host=True)
    # schedule6.agent = agent5
    # schedule6.meeting = meeting3
    #
    # office1 = OfficeModel(time(9, 0), time(19, 0))
    # agent1.offices.append(office1)
    #
    # office2 = OfficeModel(time(10, 0), time(22, 0))
    # agent2.offices.append(office2)
    #
    # office3 = OfficeModel(time(9, 0), time(12, 0))
    # office4 = OfficeModel(time(13, 0), time(19, 0))
    # agent3.offices.append(office3)
    # agent3.offices.append(office4)
    #
    # office5 = OfficeModel(time(8, 0), time(22, 0))
    # agent4.offices.append(office5)
    #
    # office6 = OfficeModel(time(8, 0), time(12, 0))
    # office7 = OfficeModel(time(14, 0), time(20, 0))
    # agent5.offices.append(office6)
    # agent5.offices.append(office7)
    #
    # preference1 = PreferenceModel(time(19, 0), time(22, 0), 1, False)
    # agent2.preferences.append(preference1)
    #
    # preference2 = PreferenceModel(time(9, 0), time(11, 0), 0, True, date(2021, 8, 8))
    # agent3.preferences.append(preference2)
    #
    # preference3 = PreferenceModel(time(11, 0), time(13, 0), 1, False)
    # preference4 = PreferenceModel(time(20, 0), time(22, 0), 0, True, date(2021, 8, 18))
    # agent4.preferences.append(preference3)
    # agent4.preferences.append(preference4)
    #
    # preference5 = PreferenceModel(time(18, 0), time(20, 0), 1, False)
    # agent5.preferences.append(preference5)
    #
    # db.session.add_all([agent1, agent2, agent3, agent4, agent5])
    # db.session.add_all([meeting1, meeting2, meeting3])
    # db.session.add_all([schedule1, schedule2, schedule3, schedule4, schedule5, schedule6, schedule7, schedule8])
    # db.session.add_all([office1, office2, office3, office4, office5, office6, office7])
    # db.session.add_all([preference1, preference2, preference3, preference4, preference5])
    #
    # db.session.commit()

    # init agents and current agent
    agents = AgentModel.query.all()

    return render_template('index.html', agents=agents, agent=None)


@app.route('/agent/<int:aid>', methods=['GET'])
def agent(aid):
    # init agents and current agent
    agents = AgentModel.query.all()
    agent = AgentModel.query.get(aid)

    # get other agents except self, for meeting request
    others = AgentModel.query.filter(AgentModel.agent_id != agent.agent_id).all()

    # get meeting ids for current agent
    mids = []
    for meeting in agent.meetings:
        mids.append(meeting.meeting_id)

    # get meetings
    meetings = MeetingModel.query.filter(MeetingModel.meeting_id.in_(mids)).order_by(
        MeetingModel.start_time.asc()).all()
    if len(meetings) == 0:
        meetings = None

    # get offices
    offices = OfficeModel.query.filter(OfficeModel.agent_id == aid).order_by(OfficeModel.start_time.asc()).all()
    if len(offices) == 0:
        offices = None

    # get preferences
    preferences = PreferenceModel.query.filter(PreferenceModel.agent_id == aid).order_by(PreferenceModel.is_local.asc(),
                                                                                         PreferenceModel.start_time.asc()).all()
    if len(preferences) == 0:
        preferences = None

    return render_template('agent.html', agents=agents, agent=agent
                           , others=others, meetings=meetings, offices=offices, preferences=preferences)


@app.template_filter('split_name')
def split_name(email):
    """
    filter, split the email prefix
    :param email:
    :return:
    """
    return email.split('@')[0]


@app.template_filter('start_cut')
def start_cut(dt):
    """
    filter, format the datetime to date and time
    :param dt:
    :return:
    """
    return dt.strftime('%m/%d/%Y %H:%M')


@app.template_filter('end_cut')
def end_cut(dt):
    """
    filter, format the datetime to time
    :param dt:
    :return:
    """
    return dt.strftime('%H:%M')


if __name__ == '__main__':
    app.run(debug=True)
