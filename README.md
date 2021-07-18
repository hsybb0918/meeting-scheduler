# Multi-Agent Meeting Scheduler

Project entry: ```app.py```.

Three negotiation strategies are implemented in the project and several scenarios are used to test the the whole negotiation algorithm.

The project uses ```SPADE``` to realize the multi-agent environment and focuses on Object Oriented Programming (OOP) that relies on the concept of classes and objects.

## Negotiation strategies

Three negotiation strategies are implemented in the multi-agent meeting scheduler: simple match strategy, counterproposal strategy and voting strategy.

Every agent has their own belief base (office time and priorities over days and time slots). Every priority is defined by an integer value that varies between 0 and 10, in which 0 represents the lowest priority (unavailable) and 10 the highest (5 by default). For example, some people prefer not to attend meetings at weekends or lunch time, therefore the time slots scheduled at weekends or lunch time can either be unavailable (zero) or have a low priority value. 

#### Classes

Each agent has its own calendar and do not know other agents' calendar. The project mainly has the following classes to manage the calendar.

##### UserCalendar

+ schedules: list[ScheduledMeeting]
+ offices: list[OfficeTime]
+ preferences: list[PreferenceTime]

##### ScheduledMeeting

+ start_time: datetime.time
+ end_time: datetime.time
+ subject: str
+ location: str
+ description: str
+ host_agent: str
+ guest_agents: list[str]

##### OfficeTime

+ start_time: datetime.time
+ end_time: datetime.time

##### PreferenceTime

+ start_time: datetime.time
+ end_time: datetime.time
+ priority: int
+ is_local: bool
+ specified_date: datetime.date

#### Strategy 1: simple match strategy

The host agent proposes a meeting and sends the request to all the guest agents. When a guest agent receives the meeting request, it will access the belief base and find if the requested meeting time can be accepted. Each guest agent replies to the host agent whether the proposed time is available.

After the host agent receives all the replies,
+ if all the guest agents are available at the proposed time, the host agent informs that the meeting is successfully scheduled.
+ if one of the guest agents is unavailable at the proposed time, the counterproposal strategy will be applied.

#### Strategy 2: counterproposal strategy

The host agent tells the guest agents that they did not reach an agreement on the initial proposed time. Once the message is received by a guest agent, it creates a counterproposal and sends 5 available time slots that have the highest preference value and are closest to the initial proposed time to the host agent. To avoid searching through all the slots, this strategy only considers available slots of the day that the meeting was originally proposed.

After the host agent receives all the replies, 
+ if there is a common available time for all participants, the host agent chooses the time with the highest total preference value and informs that the meeting is successfully scheduled.
+ if there is no such time, the voting strategy will be applied.

#### Strategy 3: voting strategy

The voting strategy is the last resort for the agents to find a meeting slot when other strategies fails. The host agent finds 10 time slots on that day and sends to the guest agents. Each guest agent votes on each time, informing the host agent if the time is available and the preference of that time.

Once all the guest agents respond to the host agent, the host agent picks the time when the most participants are available and the total preference value is the highest.