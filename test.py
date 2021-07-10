# @File        : test.py
# @Description :
# @Time        : 07 July, 2021
# @Author      : Cyan

from datetime import datetime, timedelta

appointments = [(datetime(2012, 5, 22, 10), datetime(2012, 5, 22, 10, 30)),
                (datetime(2012, 5, 22, 12), datetime(2012, 5, 22, 13)),
                (datetime(2012, 5, 22, 15, 30), datetime(2012, 5, 22, 17, 00))]

hours = (datetime(2012, 5, 22, 9), datetime(2012, 5, 22, 20))

def get_slots(hours, appointments, duration=timedelta(hours=1), division=timedelta(minutes=30)):
    slots = sorted([(hours[0], hours[0])] + appointments + [(hours[1], hours[1])])
    for start, end in ((slots[i][1], slots[i+1][0]) for i in range(len(slots)-1)):
        # print(start, end)
        assert start <= end, "Cannot attend all appointments"
        # print(start+duration)
        while start + duration <= end:
            print("{:%H:%M} - {:%H:%M}".format(start, start + duration))
            start += division

if __name__ == "__main__":
    get_slots(hours, appointments)
