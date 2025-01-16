from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer
from qiskit.quantum_info import random_statevector
from qiskit.primitives import Sampler
import numpy as np

class QuantumKeyGenerator:
    def __init__(self):
        self.backend = Aer.get_backend('aer_simulator')
        self.sampler = Sampler()
    
    def check_quantum_noise(self):
        """Simulate quantum noise detection"""
        # This is a simplified simulation of noise detection
        # In a real quantum system, you would measure actual noise levels
        return np.random.random() * 0.05  # Returns a value between 0 and 0.05
    
    def generate_random_bits(self, num_bits):
        """Generate random bits for the key"""
        return np.random.randint(2, size=num_bits, dtype=np.int32)
    
    def generate_random_bases(self, num_bases):
        """Generate random bases (0 for computational, 1 for Hadamard)"""
        return np.random.randint(2, size=num_bases, dtype=np.int32)
    
    def prepare_qubits(self, bits, bases):
        """Prepare qubits according to bits and bases"""
        n = len(bits)
        qr = QuantumRegister(n)
        cr = ClassicalRegister(n)
        qc = QuantumCircuit(qr, cr)
        
        for i in range(n):
            if bits[i]:
                qc.x(qr[i])
            if bases[i]:
                qc.h(qr[i])
                
        return qc
    
    def measure_qubits(self, circuit, bases):
        """Measure qubits in specified bases"""
        circuit = circuit.copy()
        n = len(bases)
        for i in range(n):
            if bases[i]:
                circuit.h(i)
            circuit.measure(i, i)
            
        return circuit 