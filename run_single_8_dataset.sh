#PBS -N single_8_dataset
#PBS -m ae
#PBS -M fmohammadi@ce.sharif.edu
#PBS -l nodes=1:ppn=1
cd GKmerhood
/share/apps/Anaconda/anaconda3.7/bin/python3.7 GKmerhood.py > single_8_dataset.output
