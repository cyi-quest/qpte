import pennylane as qml
import numpy as np

class Circuit:
    def __init__(self, qubits):
        self.dev = qml.device("default.qubit", wires=qubits)
        self.state = np.zeros(2**len(self.dev.wires))
        self.state[0] = 1

    def amplitudes(self, wires):
        """
        :param wires: Indices of qubits whose states' probability amplitudes are to be found
        :return: The probability amplitudes states of qubits `wires`, for the quantum state vector `psi`
        """
        @qml.qnode(self.dev)
        def probs():
            qml.StatePrep(self.state, wires=self.dev.wires)
            return qml.probs(wires=wires)
        return np.array(probs())

    def measure(self, qubit, result=None):
        """
        Modifies the local state, by collapsing `qubit`. If specified, `result` forces the outcome of the measurement.
        Otherwise, this is determined by the probability amplitudes of the two states of the qubit.
        :param qubit: Index of the qubit to measure.
        :param result: Optional, 0 or 1. Forces the outcome of the measurement to the specified value.
        :return: A tuple with the probability of `qubit` collapsing to 1, and the result (0 or 1) of the measurement.
        """
        prob_wire_is_1 = self.amplitudes(qubit)[1]
        if result is None:
            result = int(np.random.rand() < prob_wire_is_1)
        chunks = np.array(np.split(self.state, 2 ** (qubit + 1)))
        chunks[(1 - result):len(chunks):2] *= 0
        self.state = np.concatenate(chunks)
        self.state /= np.linalg.norm(self.state)
        return prob_wire_is_1, result

    def hadamard(self, qubits):
        """
        Modifies the local state by applying a Hadamard gate to all qubits.
        :param qubits: The indices of the qubits to apply the hadamard gate to.
        """
        @qml.qnode(self.dev)
        def local_hadamard():
            qml.StatePrep(self.state, wires=self.dev.wires)
            for qubit in qubits:
                qml.Hadamard(wires=[qubit])
            return qml.state()
        self.state = np.array(local_hadamard())

    def reset(self, qubit, qubit_is_1):
        """
        Modifies the local state by applying an X gate to `qubit`, if `qubit_is_1` is True.
        :param qubit: Index of the qubit to reset.
        :param qubit_is_1: Whether to reset the qubit.
        """
        @qml.qnode(self.dev)
        def local_reset():
            qml.StatePrep(self.state, wires=self.dev.wires)
            qml.X(qubit)
            return qml.state()

        if qubit_is_1 == 1:
            self.state = np.array(local_reset())
    #
    # def qft(self, wires, target):
    #     @qml.qnode(self.dev)
    #     def local_qft():
    #         qml.StatePrep(self.state, wires=self.dev.wires)
    #         for j in range(len(wires)):
    #             qml.Hadamard(wires=[wires[j]])
    #             for k in range(j + 1, len(wires)):
    #                 theta = 2 * np.pi / 2 ** (1 + k - j)
    #                 qml.ControlledQubitUnitary(
    #                     [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]],
    #                     control_wires=[wires[j], wires[k]],
    #                     control_values=[1, 1],
    #                     wires=[target]
    #                 )
    #         for j in range(len(wires) // 2):
    #             qml.SWAP(wires=[wires[j], wires[- j - 1]])
    #         return qml.state()
    #     self.state = np.array(local_qft())

    def qft(self, wires, target, control_qubits=None, control_values=None):
        if control_qubits is None:
            control_qubits = []
        if control_values is None:
            control_values = []

        @qml.qnode(self.dev)
        def local_qft():
            qml.StatePrep(self.state, wires=self.dev.wires)
            inv_sqrt_2 = 1/np.sqrt(2)
            h = [[inv_sqrt_2, inv_sqrt_2], [inv_sqrt_2,-inv_sqrt_2]]
            for j in range(len(wires)):
                qml.ControlledQubitUnitary(
                    h,
                    control_wires=control_qubits,
                    control_values=control_values,
                    wires=[wires[j]]
                )
                for k in range(j + 1, len(wires)):
                    theta = 2 * np.pi / 2 ** (1 + k - j)
                    qml.ControlledQubitUnitary(
                        [ [np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)] ],
                        control_wires=list(control_qubits) + [wires[j], wires[k]],
                        control_values=list(control_values) + [1, 1],
                        wires=[target]
                    )
            for j in range(len(wires) // 2):
                swap = [
                    [1, 0, 0, 0],
                    [0, 0, 1, 0],
                    [0, 1, 0, 0],
                    [0, 0, 0, 1],
                ]
                qml.ControlledQubitUnitary(
                    swap,
                    control_wires=control_qubits,
                    control_values=control_values,
                    wires=[wires[j], wires[- j - 1]]
                )
            return qml.state()
        self.state = np.array(local_qft())

    def iqft(self, wires, target):
        @qml.qnode(self.dev)
        def circuit():
            qml.StatePrep(self.state, wires=self.dev.wires)
            for j in range(len(wires) // 2):
                qml.SWAP(wires=[wires[j], wires[len(wires) - j - 1]])
            for j in reversed(range(len(wires))):
                for k in reversed(range(j + 1, len(wires))):
                    theta = - 2 * np.pi / 2 ** (1 + k - j)
                    qml.ControlledQubitUnitary(
                        [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]],
                        control_wires=[wires[j], wires[k]],
                        control_values=[1, 1],
                        wires=[target]
                    )
                qml.Hadamard(wires=[wires[j]])
            return qml.state()
        self.state = np.array(circuit())

    def apply(self, circuit, *args, **kwargs):
        @qml.qnode(self.dev)
        def application():
            qml.StatePrep(self.state, self.dev.wires)
            circuit(*args, **kwargs)
            return qml.state()
        self.state = np.array(application())