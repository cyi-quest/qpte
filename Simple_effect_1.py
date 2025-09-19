#!/usr/bin/env python
# coding: utf-8

# # Quantumadio Effects With Batch Streams
# 
# The examples below take us one step further into signal processing, by making a more dynamical and parameterized changes using the `batch` processing mode.
# 
# 

# #### Import _quantumaudio_ and necessary _tools_

# Set path for local use of the repository
import os
import sys
sys.path.insert(0, os.path.dirname(os.getcwd()))


import quantumaudio


from tools.audio import read, write
from tools.interactive import play, compare_audio
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt


# ## Effect 1 - Dinamically rotating the channel register

# #### Load a Stereo Audio

sound_bank = "destrair_sounds"
file_name = "Destraido_CycloBell_banco_A_07.wav"
path = f"{sound_bank}/{file_name}"

y, sr = read(path,mono=False)

def batch_proc_channel_rot(chunks, scheme, backend=None):
    output = []
    chunks_size = len(chunks)
    rotation_multiplier = 10
    
    #tqdm is used to show a progress bar. It is optional.
    for i, chunk in enumerate(tqdm(chunks)):
        # encode
        circuit = scheme.encode(chunk, verbose=0, measure=False)
        channel_qubit_index = circuit.metadata["qubit_shape"][0] + 1 #channel qubit follows index qubit

        # Slowly change the probability of measuring the right channel
        circuit.ry((rotation_multiplier*i/chunks_size)*np.pi,channel_qubit_index)

        # decode
        shots=10000 #Remember that shots==0 returns an error!


        #dummy output to test if code without running the quantum simulation
        #output.append(np.zeros(len(chunk))) 

        # Real Simulation
        output.append(scheme.decode(circuit, backend=backend, shots=shots))    # quantum simulation occurs here
    
    return output


# #### Perform Batch processing (WARNING: this may take a several minutes to run on a laptop)


# Run it yourself, test with different chunk sizes. Also test with 'msqm' and 'msqpam' schemes.
y_out = quantumaudio.stream(y, scheme='mqsm', chunk_size=64, process_function=batch_proc_channel_rot, batch_process=True)

multiplier = 10

write(y_out, sr, f"destrair_outputs/{file_name}_channel_rot_mul{multiplier}.wav") 


