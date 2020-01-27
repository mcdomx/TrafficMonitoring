import time


class ElapsedTime:
    def __init__(self, start_time=time.perf_counter()):
        self.start_time = start_time

    def get(self):
        return time.perf_counter() - self.start_time

    def __str__(self):
        t = self.get()
        s = int(t % 60)
        m = int((t / 60) % 60)
        h = int((t / (60 * 60)) % 60)
        return "{:02}:{:02}:{:02}".format(h, m, s)

    def __round__(self, x):
        return self.__str__()
