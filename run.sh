#!/bin/bash

for ((CPUS_PER_TASK=1; CPUS_PER_TASK<=32; CPUS_PER_TASK*=2)); do
  for ((QPTE_BLOCK_SIZE=64; QPTE_BLOCK_SIZE<=8192; QPTE_BLOCK_SIZE*=2)); do
    export QPTE_BLOCK_SIZE

    printf -v DATA_PATH "%s/data/pass-cpus_%02d-block_size_%04d" $(pwd) $CPUS_PER_TASK $QPTE_BLOCK_SIZE
    echo $CPUS_PER_TASK $QPTE_BLOCK_SIZE > $DATA_PATH

    srun \
      --job-name=qpte-${CPUS_PER_TASK}-${QPTE_BLOCK_SIZE} \
      --time=00:30:00 \
      --output="logs/qpte-${CPUS_PER_TASK}-${QPTE_BLOCK_SIZE}.out" \
      --error="logs/qpte-${CPUS_PER_TASK}-${QPTE_BLOCK_SIZE}.err" \
      --ntasks=1 \
      --cpus-per-task=$CPUS_PER_TASK \
      --mem=16G \
      -- \
      bash -l -c "module load Python/3.10 && source .venv/bin/activate && PYTHONPATH=$(pwd) python experiments/pass.py >> $DATA_PATH"
  done
done