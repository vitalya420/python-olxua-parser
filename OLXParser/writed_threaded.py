from queue import Queue
from threading import Thread

from .writer import CSVWriter


class CSVWriterThreaded(CSVWriter, Thread):
    def __init__(self, filename):
        super().__init__(filename)
        Thread.__init__(self)
        self.write_queue = Queue()
        self.running = False

    def append(self, data):
        self.write_queue.put(data)

    def run(self):
        self.running = True
        while self.running:
            if not self.write_queue.empty():
                self.write(self.write_queue.get())

    def stop(self):
        self.running = False
