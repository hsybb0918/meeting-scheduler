from datetime import datetime, time, date

from flask import Flask, render_template

from apps import create_app
from models.meeting_agent import MeetingAgent
from models.user_calendar import ScheduledMeeting
from apps.models.models import ScheduleModel, AgentModel, MeetingModel, OfficeModel, PreferenceModel

from apps import db

app = create_app()

agents = []


@app.before_first_request
def init_agents():
    agent1 = MeetingAgent('meeting-alice@404.city', 'meeting-alice')
    agents.append(agent1)

    agent2 = MeetingAgent('meeting-bob@404.city', 'meeting-bob')
    agents.append(agent2)

    agent3 = MeetingAgent('meeting-calvin@404.city', 'meeting-calvin')
    agents.append(agent3)

    agent1.start()
    agent2.start()
    agent3.start()


@app.route('/')
def hello_world():
    # db.create_all()

    # db.session.add(AgentModel('meeting-alice@404.city', 'meeting-alice'))
    # db.session.add(AgentModel('meeting-bob@404.city', 'meeting-bob'))
    # db.session.add(AgentModel('meeting-calvin@404.city', 'meeting-calvin'))

    # agent1 = AgentModel('meeting-alice@404.city', 'meeting-alice')
    # agent2 = AgentModel('meeting-bob@404.city', 'meeting-bob')
    # agent3 = AgentModel('meeting-calvin@404.city', 'meeting-calvin')
    #
    # meeting1 = MeetingModel(datetime(2021, 7, 28, 11, 0), datetime(2021, 7, 28, 12, 0), 'Calendar project')
    # meeting2 = MeetingModel(datetime(2021, 8, 8, 14, 0), datetime(2021, 8, 8, 16, 0), 'Go to the movie', '', 'Tenet')
    #
    # schedule1 = ScheduleModel(is_host=True)
    # schedule1.agent = agent1
    # schedule1.meeting = meeting1
    #
    # schedule2 = ScheduleModel(is_host=False)
    # schedule2.agent = agent2
    # schedule2.meeting = meeting1
    #
    # schedule3 = ScheduleModel(is_host=False)
    # schedule3.agent = agent3
    # schedule3.meeting = meeting1
    #
    # schedule4 = ScheduleModel(agent_id=agent1.agent_id, meeting_id=meeting2.meeting_id, is_host=False)
    # schedule4.agent = agent1
    # schedule4.meeting = meeting2
    #
    # schedule5 = ScheduleModel(agent_id=agent2.agent_id, meeting_id=meeting2.meeting_id, is_host=True)
    # schedule5.agent = agent2
    # schedule5.meeting = meeting2
    #
    # office1 = OfficeModel(time(9, 0), time(17, 0))
    # agent1.offices.append(office1)
    # office2 = OfficeModel(time(10, 0), time(22, 0))
    # agent2.offices.append(office2)
    #
    # office3 = OfficeModel(time(9, 0), time(12, 0))
    # office4 = OfficeModel(time(13, 0), time(17, 0))
    # agent3.offices.append(office3)
    # agent3.offices.append(office4)
    #
    # preference1 = PreferenceModel(time(19, 0), time(22, 0), 2, False)
    # agent2.preferences.append(preference1)
    #
    # preference2 = PreferenceModel(time(9, 0), time(11, 0), 0, True, date(2021, 8, 8))
    # agent3.preferences.append(preference2)
    #
    # db.session.add_all([agent1, agent2, agent3])
    # db.session.add_all([meeting1, meeting2])
    # db.session.add_all([schedule1, schedule2, schedule3, schedule4, schedule5])
    # db.session.add_all([office1, office2, office3, office4])
    # db.session.add_all([preference1, preference2])
    #
    # db.session.commit()

    print('hello', db.engine)
    # global agent_1
    # global agent_2
    # global agent_3
    # agent_1.start()
    # agent_2.start()
    # agent_3.start()

    # global agents
    # for agent in agents:
    #     agent.start()
    # agent_2.set_time_slots_preference({23: 0})

    print(len(agents))

    return render_template('agent.html', agents=agents)


@app.route('/foo', methods=['GET', 'POST'])
def foo():
    global agent_1
    global agent_2
    global agent_3

    meeting = ScheduledMeeting(6, 30, 2021)
    meeting.set_time_slots(23, 24)
    meeting.set_participants('meeting-alice@404.city', 'meeting-bob@404.city', 'meeting-calvin@404.city')
    meeting.set_information('master thesis', 'ms team', 'talk about the project')

    agent_1.propose_meeting(meeting)

    # print(meeting)

    return 'yes'


if __name__ == '__main__':
    app.run(debug=True)
