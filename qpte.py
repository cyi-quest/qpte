from os import getenv
from contextlib import ExitStack
from concurrent.futures import ProcessPoolExecutor
from soundfile import SoundFile

class Block:
    def __init__(self, index, data, qubit_requirements):
        self.index = index
        self.data = data
        self.qubit_requirements = qubit_requirements

def blocks(input_file, block_size, overlap):
    qubit_requirements = 1
    while 2**qubit_requirements < block_size:
        qubit_requirements += 1
    for index, data in enumerate(input_file.blocks(blocksize=block_size, overlap=overlap)):
        yield Block(index, data, qubit_requirements)

def environment_number(variable_name):
    try:
        value = getenv(variable_name)
        return value and int(value)
    except ValueError:
        return None

def parallelize(input_file_path, output_file_paths, process, overlap=0):
    n_proc = environment_number('SLURM_CPUS_PER_TASK') or 1
    block_size = environment_number('QPTE_BLOCK_SIZE') or 64

    with SoundFile(input_file_path) as input_file:
        sample_rate = input_file.samplerate
        with ExitStack() as stack:
            output_files = [
                stack.enter_context(SoundFile(output_file_path, "w", sample_rate, channels=1))
                for output_file_path in output_file_paths
            ]
            with ProcessPoolExecutor(max_workers=n_proc) as executor:
                for outcomes in executor.map(process, blocks(input_file, block_size, overlap)):
                    for outcome, output_file in zip(outcomes, output_files):
                        output_file.write(outcome)