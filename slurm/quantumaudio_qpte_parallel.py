#!/usr/bin/env python
# coding: utf-8

import os
import sys
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

import quantumaudio
from tools.audio import read, write
from tools.interactive import play, compare_audio
import numpy as np
import matplotlib.pyplot as plt
import time

def process_single_chunk(args):
    chunk, i, chunks_size, scheme, backend, shots = args
    circuit1 = scheme.encode(chunk[0], verbose=0, measure=False)
    circuit2 = scheme.encode(chunk[1], verbose=0, measure=False)

    qpte = quantumaudio.utils.prepare_qpte_circuit(circuit1, circuit2)

    processed_chunk = scheme.decode_all_terms(qpte, n_of_terms=4, backend=backend, shots=shots)

    return processed_chunk

def batch_proc_qpte_parallel(chunks, scheme, backend=None, shots=10000, max_workers=None):
    chunks_size = len(chunks)
    args = [
        (chunk, i, chunks_size, scheme, backend, shots)
        for i, chunk in enumerate(chunks)
    ]
    output = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for processed_chunk in tqdm(executor.map(process_single_chunk, args), total=chunks_size):
            output.append(processed_chunk)
    return output

def qpte_post_process_chunks(x):

    y00, y01, y10, y11 = (np.concatenate(c) for c in zip(*x))
    return y00, y01, y10, y11

def main():
    # Load audio
    sound_bank = "qpte_sounds"
    file_name1 = "LFO_2.5hz_mono.wav"
    file_name2 = "Destraido_CycloBell_banco_A_01_mono.wav"
    out_name = "CycloBell_A_01_LFO_SHIFTED_Quantum"

    path1 = os.path.join(sound_bank, file_name1)
    path2 = os.path.join(sound_bank, file_name2)
    y1, sr = read(path1, mono=True)
    y2, sr = read(path2, mono=True)
    
    y = np.array([y2,y1])
    # Define processing parameters
    scheme = 'sqpam_qpte'  # or 'msqm', 'msqpam', etc.
    chunk_size = 64
    shots = 10000000
    
    # Determine max_workers from SLURM or default
    cpus_per_task = os.getenv('SLURM_CPUS_PER_TASK')
    if cpus_per_task is not None:
        max_workers = int(cpus_per_task)
    else:
        max_workers = os.cpu_count()
    
    # Perform batch processing in parallel
    start = time.perf_counter()
    y_out = quantumaudio.stream(
        y,
        scheme=scheme,
        chunk_size=chunk_size,
        process_function=lambda chunks, scheme: batch_proc_qpte_parallel(
            chunks,
            scheme=scheme,
            backend=None,  # Specify your backend if needed
            shots=shots,
            max_workers=max_workers
        ),
        batch_process=True
    )
    elapsed = time.perf_counter() - start
    parsed_out = qpte_post_process_chunks(y_out)

    # Write output
    output_dir = "qpte_outputs"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Processing time: {elapsed:.2f} seconds")
    # Save elapsed time to a file
    with open(os.path.join(output_dir,"processing_time.txt"), "a") as f:
        f.write(f"Processing time: {elapsed:.2f} seconds | chunk size: {chunk_size} | shots: {shots}\n")
    
    for i in range(4):

        output_file = f"{out_name}_qpte_size{chunk_size}_shots{shots}_{scheme}_long_term{i}.wav"
        write(parsed_out[i], sr, os.path.join(output_dir, output_file))
        print(f"Processed audio saved to {os.path.join(output_dir, output_file)}")

if __name__ == "__main__":
    main()
