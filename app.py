from time import time as currentTime
from time import strftime, gmtime
from getopt import getopt
from GKmerhood import GKmerhood
from functools import reduce
from misc import if_none_false
import sys

def single_level_dataset(kmin, kmax, level, dmax):
    print('operation SLD: generating single level dataset\n\
        arguments -> kmin=%d, kmax=%d, level=%d, distance=%d'%(kmin, kmax, level, dmax))

    last_time = currentTime()
    gkhood = GKmerhood(kmin, kmax)
    print('GKhood instance generated in %f seconds'%(currentTime() - last_time))

    last_time =  currentTime()
    gkhood.single_level_dataset(dmax, level)
    print(strftime("%H:%M:%S", gmtime(currentTime() - last_time)))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise Exception('request command must be specified (read the description for supported commands)')

    shortopt = 'd:m:M:l:'
    longopts = ['kmin=', 'kmax=', 'distance=', 'level=']
    args_dict = {}

    command = sys.argv[1]

    opts, args = getopt(sys.argv[2:], shortopt, longopts)
    for o, a in opts:
        if o in ['-m', '--kmin']:
            args_dict.update({'kmin':int(a)})
        elif o in ['-M', '--kmax']:
            args_dict.update({'kmax':int(a)})
        elif o in ['-l', '--level']:
            args_dict.update({'level':int(a)})
        elif o in ['-d', '--distance']:
            args_dict.update({'dmax':int(a)})

    try:
        if command == 'SLD':
            single_level_dataset(args_dict['kmin'], args_dict['kmax'], args_dict['level'], args_dict['dmax'])
        else:
            print('[ERROR] command %s is not supported'%command)
    except:
        print('[ERROR] missing necessery arguments. please check the description and try again')
