from twobitreader import download as twobitdownloader
import sys

from constants import TWOBIT_LOCATION


def download_2bit(name):
    twobitdownloader.save_genome(name, TWOBIT_LOCATION)


if __name__ == "__main__":
    twobitdownloader.save_genome(sys.argv[1], TWOBIT_LOCATION)