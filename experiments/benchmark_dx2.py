from qpte import parallelize, N_PROC, BLOCK_SIZE
from time import perf_counter

import numpy as np
import pennylane as qml

DEFAULT_DERIVATIVE = 2

def derivative(block, k = DEFAULT_DERIVATIVE):
    qs = np.arange(block.qubit_requirements)
    ts = len(qs) + np.arange(k)
    dev = qml.device("default.qubit", wires=len(qs) + len(ts))

    normalization_factor = np.linalg.norm(block.data)

    @qml.qnode(dev)
    def simulate_discrete_derivative():
        # 1. Prepare f = block.data, on qubit register q (of size n)
        qml.StatePrep(block.data / normalization_factor, wires=qs, pad_with=0)

        # 2. Apply DFT on q to obtain |hat(f)>
        qml.adjoint(qml.QFT(wires=qs))

        # 3. Encode the Fourier coefficients of the discrete derivative kernel
        #    using the k ancilla qubits of qubit register t
        for t in ts:
            # Apply RY(θ) to every qubit of t, where:
            # - RY(θ)|0> = cos(θ)|0> + sin(θ) |1>
            for j, q in enumerate(reversed(qs)):
                # The j-th qubit of q, corresponds to the j-th most significant bit of each basis state |x> of q
                # and contributes 2^j * π / N to the RY rotation
                theta = (2**j * np.pi) / (2**len(qs))
                qml.ctrl(
                    qml.QubitUnitary([
                        [np.cos(theta), -np.sin(theta)],
                        [np.sin(theta),  np.cos(theta)],
                    ], t),
                    control=[q]
                )
            # Apply Z(-θ) to every qubit of t, where:
            # - Z(θ)|1> = |0> + exp(iθ)|1>
            for j, q in enumerate(reversed(qs)):
                # The j-th qubit of q, contributes 2^j * π / N to the RZ rotation
                theta = (2 ** j * np.pi) / (2 ** len(qs))
                qml.ctrl(
                    qml.QubitUnitary([
                        [1, 0],
                        [0, np.exp(-1j * theta)],
                    ], t),
                    control=[q]
                )
            # Flip the angle to π/2 - θ for both the RY and RZ rotation
            qml.QubitUnitary([
                [0, 1j],
                [1j, 0],
            ], wires=[t])

        # 4. Apply DFT† on q to obtain |Δ^kf/Δx^k>
        qml.QFT(wires=qs)
        return qml.state()

    # 5. Post-select based on the outcome of the qubits of register t, and renormalize the probability distributions
    state_vector = np.array(
        simulate_discrete_derivative()
    ).reshape((2 ** len(qs), 2 ** len(ts))).T
    return np.real(state_vector * normalization_factor)



if __name__ == "__main__":
    number_of_runs = 100
    for _ in range(number_of_runs):
        start = perf_counter()
        parallelize(
            "audio/input/bell.wav",
            [f"audio/output/bell_d{DEFAULT_DERIVATIVE}_{t}_{N_PROC:>02}_{BLOCK_SIZE:>04}.wav" for t in range(2**DEFAULT_DERIVATIVE)],
            derivative
        )
        print(perf_counter() - start)
