# Multi-Agent Meeting Scheduler

Project entry: ```app.py```.

Three negotiation strategies are implemented in the project and three predefined scenarios are used to test the three strategies respectively.

The project uses ```SPADE``` to realize the multi-agent environment and focuses on Object Oriented Programming (OOP) that relies on the concept of classes and objects.

## Negotiation strategies

Three negotiation strategies are implemented in the multi-agent meeting scheduler: simple match, counterproposal strategy and voting strategy.

Every agent has their own belief base (user preferences and priorities over weekday, time slots and people). Every priority is defined by an integer value that varies between 1 and 10, in which 1 represents the maximum priority and 10 the lowest (5 by default). Foe example, some people prefer not to attend meetings at weekends or lunch time, therefore the time slots scheduled at weekends or lunch time can either be unavailable or have a low priority value. 

#### Classes

Each agent has its own calendar and do not know other agents' calendar. The project mainly has the following classes to manage the calendar.

##### ScheduledMeeting

+ Host agent that will propose a meeting
+ Guest agents that will receive a meeting proposal and respond to it
+ Date and time slots of the meeting
+ Subject of the meeting
+ Location of the meeting
+ Description of the meeting

##### ScheduledDay

+ Date
+ Unavailable time slots
+ Scheduled meetings

##### Calendar

+ Scheduled days
+ Global time slot preference
+ Global weekday preference

#### Strategy 1: simple match

The host agent proposes a meeting and sends the request to all the guest agents.

When a guest agent receives a meeting request, it will access the belief base and find if the requested meeting time can be accepted. Each guest agent replies to the host agent whether the proposed time is available.

After the host agent receives all the replies,
+ if all the guest agents are available at the proposed time, the host agent informs that the meeting is successfully scheduled.
+ if one of the guest agents is unavailable at the proposed time, the counterproposal strategy will be applied.

#### Strategy 2: counterproposal strategy

The host agent tells the guest agents that they did not reach an agreement on the initial requested time.

Once the message is received by a guest agent, it creates a counterproposal and sends 5 available time slots with their preference that have the highest preference and are closest to the initial requested time to the host agent. To avoid searching through all the slots, this strategy only considers available slots of the day that the meeting was originally proposed.

After the host agent receives all the replies, 
+ if there is a common available time for all participants, the host agent chooses the time with the highest total preference value and informs that the meeting is successfully scheduled.
+ if there is no such time, the voting strategy will be applied.

#### Strategy 3: voting strategy

The voting strategy is the last resort for the agents to find a meeting slot when other strategies fails. The host agent finds all available time slots (or 10 time slots) on that day and sends to the guest agents.

Each guest agent votes on each time, informing the host agent if the time is available and the preference of that time.

Once all the guest agents respond to the host agent, the host agent picks the time when the most participants are available and the total preference value is the highest.

## Test scenarios

During the automatic meeting scheduling process, each agent represents a specific person and communicates with other agents to to reach an agreement about the meeting time. This work assumes that a meeting is an activity that needs at least two people and has a subject to be dealt with.

In the scenarios, there are three agents that negotiation the meeting time on behalf of three people named Alice, Ben and Calvin.

#### Scenario 1

#### Scenario 2
 
#### Scenario 3

## Requirement analysis

The project utilizes feature-driven development and test-driven development. The requirement analysis is presented as follows.

+ Establish agents and realize message passing
+ Realize the first negotiation strategy and evaluate with the scenario
+ Realize the second negotiation strategy and evaluate with the scenario
+ Realize the third negotiation strategy and evaluate with the scenario
+ Implement the user interface
+ Polish the user interface
+ Improve the overall structure