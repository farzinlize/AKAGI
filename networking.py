import os
from pool import AKAGIPool
from misc import int_to_bytes, bytes_to_int, make_location
from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname
from constants import SOCKET_BUFFSIZE, NETWORK_LOG, MASTER, ASSISTANT, INT_SIZE, APPDATA_PATH

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

        checkpoint = self.recvfile_socket()

        protected_directory = APPDATA_PATH + checkpoint.split('.')[0] + '/'
        make_location(protected_directory)

        for _ in range(bytes_to_int(self.read_nbytes(INT_SIZE))):
            self.recvfile_socket()
    

    def copy_jobs(self, checkpoint): # server

        self.sendfile_socket(checkpoint)

        protected_directory = APPDATA_PATH + checkpoint.split('.')[0] + '/'
        bytefiles = os.listdir(protected_directory)

        self.connection.sendall(int_to_bytes(len(bytefiles)))
        for f in bytefiles:
            self.sendfile_socket(protected_directory + f)
            


    def report_back(self, pool:AKAGIPool):pass # client
    def get_report(self):pass  # server
    def REFUSE(self):pass # server

    def send_rest(self):pass   # client
    def receive_rest(self):pass # server


    def sendfile_socket(self, filename):
        self.connection.sendall(int_to_bytes(len(filename), int_size=1))
        self.connection.sendall(filename.encode())

        with open(filename, 'rb') as file:
            while True:
                chunk = file.read(SOCKET_BUFFSIZE)
                self.connection.sendall(int_to_bytes(len(chunk), int_size=2))
                if chunk:self.connection.sendall(chunk)
                else    :break


    def recvfile_socket(self):
        length = bytes_to_int(self.read_nbytes(1))
        filename = self.read_nbytes(length).decode()

        with open(filename, 'wb') as file:
            while True:
                length = bytes_to_int(self.read_nbytes(2))
                if length == 0:
                    break # end of file signal
                chunk = self.read_nbytes(length)
                file.write(chunk)

        return filename


class AssistanceService:

    def __init__(self, port) -> None:
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind((gethostname(), port))
        self.server.listen(5)


    def listen_for_assistance(self) -> ConnectionInterface: # server
        assistant_socket, addr = self.server.accept()

        with open(NETWORK_LOG, 'a+') as logger:
            logger.write('assistant connected from address: ' + str(addr))

        return ConnectionInterface(assistant_socket, master=True)


    @staticmethod 
    def connect_to_master(addr, is_new) -> ConnectionInterface: # client
        master = socket(AF_INET, SOCK_STREAM)
        master.connect(addr)

        return ConnectionInterface(master, is_new=is_new)
        # master.send(int_to_bytes(int(is_new), int_size=1))
        # master.





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