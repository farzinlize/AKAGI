import os
from pool import AKAGIPool
from misc import int_to_bytes, bytes_to_int, make_location
from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname
from constants import SOCKET_BUFFSIZE, NETWORK_LOG, MASTER, ASSISTANT, INT_SIZE

class ConnectionInterface:

    def __init__(self, connection: socket, master=False, is_new=True):
        self.temp = b''
        self.connection = connection

        if master:self.is_new = bool(bytes_to_int(self.read_nbytes(1)))
        else:self.connection.sendall(int_to_bytes(int(is_new), int_size=1))

        
    def read_nbytes(self, nbytes: int):

        while len(self.temp) < nbytes:
            self.temp = self.temp + self.connection.recv(SOCKET_BUFFSIZE)

        data = self.temp[:nbytes]
        self.temp = self.temp[nbytes:]
        return data


    def isNew(self):
        return self.is_new

    def get_jobs(self): # client (expect checkpoint name in return)

        checkpoint = recvfile_socket(self.connection)

        protected_directory = APPDATA_PATH + checkpoint.split('.')[0] + '/'
        make_location(protected_directory)

        for _ in range(bytes_to_int(self.read_nbytes(INT_SIZE))):
            recvfile_socket(self.connection)
    

    def copy_jobs(self, checkpoint): # server

        sendfile_socket(checkpoint, self.connection)

        protected_directory = APPDATA_PATH + checkpoint.split('.')[0] + '/'
        bytefiles = os.listdir(protected_directory)

        self.connection.sendall(int_to_bytes(len(bytefiles)))
        for f in bytefiles:
            sendfile_socket(protected_directory + f, self.connection)
            


    def report_back(self, pool:AKAGIPool):pass # client
    def get_report(self):pass  # server
    def REFUSE(self):pass # server

    def send_rest(self):pass   # client
    def receive_rest(self):pass # server


class AssistanceService:

    def __init__(self, port) -> None:
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind((gethostname(), port))
        self.server.listen(5)


    def listen_for_assistance(self) -> ConnectionInterface: # server
        assistant_socket, addr = self.server.accept()

        with open(NETWORK_LOG, 'a+') as logger:
            logger.write('assistant connected from address: ', addr)

        return ConnectionInterface(assistance_socket, master=True)


    @staticmethod 
    def connect_to_master(addr, is_new) -> ConnectionInterface: # client
        master = socket(AF_INET, SOCK_STREAM)
        master.connect(addr)

        return ConnectionInterface(master, is_new=is_new)
        # master.send(int_to_bytes(int(is_new), int_size=1))
        # master.


def sendfile_socket(filename, receiver:socket):
    receiver.sendall(filename.encode())
    with open(filename, 'rb') as file:
        while True:
            chunk = file.read(SOCKET_BUFFSIZE)
            if chunk:receiver.sendall(chunk)
            else    :break


def recvfile_socket(sender:socket, extra_tag=''):
    filename = sender.recv(SOCKET_BUFFSIZE)
    print(filename)
    filename = filename.decode()
    with open(filename + extra_tag, 'wb') as file:
        while True:
            chunk = sender.recv(SOCKET_BUFFSIZE)
            if chunk:file.write(chunk)
            else    :break
    return filename


if __name__ == '__main__':

    print(gethostbyname(gethostname()))

    port = 1090
    service = AssistanceService(port)


    assistance = service.listen_for_assistance()
    assistance.get_jobs()

    assistance.connection.close()
    # server = socket(AF_INET,SOCK_STREAM)
    # server.bind(('', port))
    # server.listen(5)

    # ass, addr = server.accept()

    # recvfile_socket(ass, '.sopy')