import time


class ElapsedTime:
    def __init__(self):
        self.start_time = time.perf_counter()

    def get(self):
        return time.perf_counter() - self.start_time
