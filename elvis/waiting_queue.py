"""Wrapper class to have a more simplistic object than queue.WaitingQueue.

TODO: Question: Is setting self.next_leave to year 9999 okay? Does the job but looks weird.
-> used to not have to check if len==0 or next_leave==None. see simulate.py, line: 89"""

import datetime


class WaitingQueue:
    """Represents the waiting queue for vehicles."""
    def __init__(self, maxsize=0, arrivals=None):

        self.queue = []
        # initialise with large enough date
        self.next_leave = datetime.datetime(9999, 1, 1)
        if arrivals is not None:
            for arrival in arrivals:
                self.queue.append(arrival)

            self.determine_next_leaving_time()
        self.maxsize = maxsize

    def enqueue(self, item):
        """Add item to queue if not already full."""
        if self.size() < self.maxsize:
            self.queue.append(item)
            self.determine_next_leaving_time()

    def dequeue(self):
        """Get next item from queue if not empty."""
        if len(self.queue) < 1:
            return None
        self.determine_next_leaving_time()
        return self.queue.pop(0)

    def size(self):
        """Get number of item in queue."""
        return len(self.queue)

    def determine_next_leaving_time(self):
        """Determine the next departure time of all queued vehicles."""
        if self.size() > 0:
            leaving_times = []
            for event in self.queue:
                arrival_time = event.arrival_time
                parking_time = datetime.timedelta(hours=event.parking_time)

                leaving_times.append(arrival_time + parking_time)
            self.next_leave = sorted(leaving_times)[0]
        else:
            # if len = 0: Set next leave to be large enough date
            self.next_leave = datetime.datetime(9999, 1, 1)

    def empty(self):
        """Disconnect all vehicles currently enqueued"""
        self.queue = []
