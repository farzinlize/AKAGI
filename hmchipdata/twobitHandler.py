from twobitreader import download as twobitdownloader
import sys


def download_2bit(name):
    twobitdownloader.save_genome(name, './2bits/')


if __name__ == "__main__":
    twobitdownloader.save_genome(sys.argv[1], './2bits/')