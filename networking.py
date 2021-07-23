import os
from pool import AKAGIPool, get_AKAGI_pools_configuration
from misc import int_to_bytes, bytes_to_int, make_location
from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname
from constants import SOCKET_BUFFSIZE, NETWORK_LOG, INT_SIZE, APPDATA_PATH

class ConnectionInterface:

    def __init__(self, connection: socket, master=False, is_new=True):
        self.temp = b''
        self.connection = connection
        self.checkpoint = ''

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

    def get_checkpoint(self, working_on_it):

        checkpoint = self.recvfile_socket()
        if not checkpoint:
            return None # connection refused

        if working_on_it:self.checkpoint = checkpoint

        protected_directory = APPDATA_PATH + checkpoint.split('.')[0] + '/'
        make_location(protected_directory)

        for _ in range(bytes_to_int(self.read_nbytes(INT_SIZE))):
            self.recvfile_socket()
    

    def copy_checkpoint(self, checkpoint):

        self.sendfile_socket(checkpoint)

        protected_directory = APPDATA_PATH + checkpoint.split('.')[0] + '/'
        bytefiles = os.listdir(protected_directory)

        self.connection.sendall(int_to_bytes(len(bytefiles)))
        for f in bytefiles:
            self.sendfile_socket(protected_directory + f)
            

    # master.report_back(BEST_PATTERNS_POOL%(PC_NAME, os.getpid()))
    def report_back(self, pool_file:str, finish_code:int): # client

        # send pool data
        self.copy_checkpoint(pool_file)

        # send working checkpoint name
        self.connection.sendall(int_to_bytes(len(self.checkpoint.encode()), int_size=1))
        self.connection.sendall(self.checkpoint.encode())

        # send finish code
        self.connection.sendall(int_to_bytes(finish_code, int_size=1, signed=True))

        

    # working_checkpoint, report, finish_code = assistance.get_report()
    def get_report(self): # server

        # receive pool data
        poolfile = self.get_checkpoint()
        pool = AKAGIPool(get_AKAGI_pools_configuration())
        pool.readfile(poolfile)

        # receive working checkpoint name
        length = bytes_to_int(self.read_nbytes(1))
        working_checkpoint = self.read_nbytes(length).decode()

        # receive finish code
        finish_code = bytes_to_int(self.read_nbytes(1), signed=True)

        return working_checkpoint, pool, finish_code


    def REFUSE(self): # server
        self.connection.sendall(int_to_bytes(0, int_size=1)) # send no file signal

    # def send_rest(self):pass   # client
    # def receive_rest(self):pass # server


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
        if length == 0:return None # no file to receive

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

        with open(NETWORK_LOG, 'a') as logger:
            logger.write('assistant connected from address: ' + str(addr) + '\n')

        return ConnectionInterface(assistant_socket, master=True)


    @staticmethod 
    def connect_to_master(addr, is_new) -> ConnectionInterface: # client
        master = socket(AF_INET, SOCK_STREAM)
        master.connect(addr)

        return ConnectionInterface(master, is_new=is_new)


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