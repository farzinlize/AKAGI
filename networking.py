from pool import AKAGIPool
import socket

class ConnectionInterface:

    def __init__(self):pass

    def isNew(self):
        return self.is_new

    def get_jobs(self):pass  # client
    def copy_jobs(self):pass   # server

    def report_back(self, pool:AKAGIPool):pass # client
    def get_report(self):pass  # server
    def REFUSE(self):pass # server

    def send_rest(self):pass   # client
    def receive_rest(self):pass # server


def listen_for_assistance() -> ConnectionInterface:pass # server
def connect_to_master(addr, is_new) -> ConnectionInterface:pass # client


def assist(addr, ncores, gap, overlap):pass
