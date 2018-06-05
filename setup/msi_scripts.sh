# Install Panoptes Client to user home directory
module load python3
pip install --user --upgrade panoptes-client

#####################################
# MSI
#####################################

# Connect to Computing nodes
ssh itasca
ssh mesabi

# request interactive job
qsub -I -l nodes=1:ppn=8:gpus=1,walltime=180:00 -q k40

# run script
qsub file_name.pbs
