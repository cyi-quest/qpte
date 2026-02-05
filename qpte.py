from concurrent.futures.thread import ThreadPoolExecutor
from os import getenv
from contextlib import ExitStack
from concurrent.futures import ProcessPoolExecutor
from soundfile import SoundFile

def environment_number(variable_name):
    try:
        value = getenv(variable_name)
        return value and int(value)
    except ValueError:
        return None

def to_iterator(values):
    try:
        return iter(values)
    except TypeError:
        return iter([values])

def parallelize(input_file_path, output_file_paths, process):
    n_proc = environment_number('SLURM_CPUS_PER_TASK') or 1
    block_size = environment_number('QPTE_BLOCK_SIZE') or 64

    with SoundFile(input_file_path) as input_file:
        sample_rate = input_file.samplerate
        with ExitStack() as stack:
            output_files = [
                stack.enter_context(SoundFile(output_file_path, "w", sample_rate, channels=1))
                for output_file_path in to_iterator(output_file_paths)
            ]
            with ProcessPoolExecutor(max_workers=n_proc) as executor:
                for outcomes in executor.map(process,input_file.blocks(blocksize=block_size)):
                    for outcome, output_file in zip(to_iterator(outcomes), output_files):
                        output_file.write(outcome)