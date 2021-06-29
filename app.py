from flask import Flask, render_template

from models.meeting_agent import MeetingAgent
from models.user_calendar import ScheduledMeeting, ScheduledDay

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')

host_agent = MeetingAgent('meeting-alice@404.city', 'meeting-alice')
# host_agent.start()

guest_agent_1 = MeetingAgent('meeting-bob@404.city', 'meeting-bob')
# guest_agent_1.start()

guest_agent_2 = MeetingAgent('meeting-calvin@404.city', 'meeting-calvin')


# guest_agent_2.start()


@app.route('/')
def hello_world():
    global host_agent
    global guest_agent_1
    global guest_agent_2
    host_agent.start()
    guest_agent_1.start()
    guest_agent_2.start()
    return render_template('index.html', msg='agent')


@app.route('/foo', methods=['GET', 'POST'])
def foo():
    global host_agent
    global guest_agent_1
    global guest_agent_2

    meeting = ScheduledMeeting('master thesis', 'ms team', 'talk about the project')
    meeting.set_date(2021, 6, 30)
    meeting.set_time_slots(23, 24)
    meeting.set_participants(host_agent.jid, guest_agent_1.jid, guest_agent_2.jid)

    host_agent.propose_meeting(meeting)

    # print(meeting)

    return 'yes'


if __name__ == '__main__':
    app.run(debug=True)
