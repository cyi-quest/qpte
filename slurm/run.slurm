#!/bin/bash
#SBATCH --job-name=quantumaudio_parallel
#SBATCH --output=quantumaudio_parallel_%j.out
#SBATCH --error=quantumaudio_parallel_%j.err
#SBATCH --time=00:30:00
#SBATCH -A p233
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G

module load Python/3.10

source .venv/bin/activate

export OMP_NUM_THREADS=1            # Prevent OpenMP from oversubscribing

python quantumaudio_parallel.py