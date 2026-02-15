#!/bin/bash

CURRENT_PATH=${PWD}
CURRENT_FOLDER=${PWD##*/}
if [ "$CURRENT_FOLDER" != "experiments" ]; then
  echo "Changing directory to: $(pwd)/experiments"
  cd experiments 2>/dev/null || { \
    echo "Error: Invalid directory" 1>&2 && \
    echo "Please run the script from the repository's root or \"experiments\" folder" 1>&2 && \
    exit -1 \\
  }
fi

for ((CPUS_PER_TASK=1; CPUS_PER_TASK<=32; CPUS_PER_TASK*=2)); do
  for ((QPTE_BLOCK_SIZE=64; QPTE_BLOCK_SIZE<=8192; QPTE_BLOCK_SIZE*=2)); do
    export QPTE_BLOCK_SIZE
    export AUDIO_OUTPUT_SUFFIX="cpus_${CPUS_PER_TASK}_block_size_${QPTE_BLOCK_SIZE}"
    printf -v DATA_PATH "%s/data/pass-cpus_%02d-block_size_%04d" $(pwd) $CPUS_PER_TASK $QPTE_BLOCK_SIZE
    echo $CPUS_PER_TASK $QPTE_BLOCK_SIZE > $DATA_PATH

    echo "Running job with ${CPUS_PER_TASK} cpus for a blocksize of ${QPTE_BLOCK_SIZE}"
    srun \
      --job-name=qpte-${CPUS_PER_TASK}-${QPTE_BLOCK_SIZE} \
      --time=00:30:00 \
      --output="logs/qpte-${CPUS_PER_TASK}-${QPTE_BLOCK_SIZE}.out" \
      --error="logs/qpte-${CPUS_PER_TASK}-${QPTE_BLOCK_SIZE}.err" \
      --ntasks=1 \
      --cpus-per-task=$CPUS_PER_TASK \
      --mem=16G \
      -- \
      bash -l -c "module load Python/3.12 && source ../.venv/bin/activate && PYTHONPATH=$(pwd) python pass.py >> $DATA_PATH"
  done
done

if [ "$(pwd)" != "$CURRENT_PATH" ]; then
  echo "Changing directory to: $CURRENT_PATH"
  cd $CURRENT_PATH
fi
