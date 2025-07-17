from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import random
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import time
import sys
import pandas as pd

#----------------------------------------
# Auxiliary functions
#----------------------------------------
def quantum_random_binary_string(length):
    '''
    Random key generator using quantum randomness.
    '''
    string = []
    for bit in range(length):
        qcoin = QuantumCircuit(1,1)
        qcoin.h(0)
        qcoin.measure(0,0)
        exec = sim.run(qcoin, shots=1).result()
        string.append(int(list(exec.get_counts(qcoin).keys())[0]))
    return string


def psi_gen(a, b):
    '''
    Generation of the quantum state |psi>.
    '''
    if len(a) != len(b):
        raise ValueError('Same number of b and bits expected.')
    psi = []
    for i in range(len(a)):
        qubit = QuantumCircuit(1, 1)
        if a[i] == 1:
            qubit.x(0)
            if np.random.choice([0, 1], p=[1 - pbit, pbit]):
                qubit.x(0)
            if np.random.choice([0, 1], p=[1 - pphase, pphase]):
                qubit.z(0)
        if b[i] == 1:
            qubit.h(0)
        psi.append(qubit)
    return psi

def challenge_gen(psi, c, b):
    '''
    Generation of the challenge for |psi>.
    '''
    if len(psi) != len(c):
        raise ValueError('Same number of qubits and bits expected.')
    for i in range(len(psi)):
        if c[i] == 1:
            if b[i]==0:
                psi[i].x(0)
                if np.random.choice([0, 1], p=[1 - pbit, pbit]):
                    psi[i].x(0)
                if np.random.choice([0, 1], p=[1 - pphase, pphase]):
                    psi[i].z(0)
            else:
                psi[i].z(0)
                if np.random.choice([0, 1], p=[1 - pbit, pbit]):
                    psi[i].x(0)
                if np.random.choice([0, 1], p=[1 - pphase, pphase]):
                    psi[i].z(0)
    return psi

def alice_mod(psi, a, b):
    if len(psi) != len(a) or len(psi) != len(a):
        raise ValueError('Same number of qubits and bits expected.')
    a_xor_b = tuple(i ^ j for i,j in zip(a,b))
    for i in range(len(psi)):
        if b[i] == 1:
            psi[i].z(0)
            if np.random.choice([0, 1], p=[1 - pbit, pbit]):
                psi[i].x(0)
            if np.random.choice([0, 1], p=[1 - pphase, pphase]):
                psi[i].z(0)
        if a_xor_b[i] == 1:
            psi[i].h(0)
            if np.random.choice([0, 1], p=[1 - pbit, pbit]):
                psi[i].x(0)
            if np.random.choice([0, 1], p=[1 - pphase, pphase]):
                psi[i].z(0)
        if a[i] == 1:
            psi[i].z(0)
            if np.random.choice([0, 1], p=[1 - pbit, pbit]):
                psi[i].x(0)
            if np.random.choice([0, 1], p=[1 - pphase, pphase]):
                psi[i].z(0)
    return psi

def measurements(psi, b):
    '''
    Alice measures using the secret b.
    '''
    if len(psi) != len(b):
        raise ValueError('Same number of qubits and b expected.')
    results = []
    for i in range(len(psi)):
        if b[i] == 1:
            psi[i].h(0)
            if np.random.choice([0, 1], p=[1 - pbit, pbit]):
                psi[i].x(0)
            if np.random.choice([0, 1], p=[1 - pphase, pphase]):
                psi[i].z(0)
        psi[i].measure(0, 0)
        psi[i] = transpile(psi[i], sim)
        exec = sim.run(psi[i], shots=1).result()
        result = int(list(exec.get_counts(psi[i]).keys())[0])
        results.append(result)
    return results

def c_aprox_gen(results, p, a):
    '''
    Generation of the approximation c' for c.
    '''
    c_aprox = []
    for i, bit in enumerate(results):
        # if bit == a[i] gamma[i]; else !gamma[i]
        decission = int(p[i] ^ (bit != a[i]))
        c_aprox.append(decission)
    return c_aprox

def equal_entries_percentage(list1, list2):
    '''
    Percentage of equal entries.
    '''
    if len(list1) != len(list2):
        raise ValueError("The lists must have the same length.")
    equals = 0
    for (a, b) in zip(list1, list2):
        equals += int(a == b)
    return (equals / len(list1)) * 100

def random_binary_string(length):
    '''
    Pseudo random binary strings.
    '''
    return [random.choice([0, 1]) for _ in range(length)]

def loading_bar(iteration, total, start_time, prefix='Progress:', length=50, fill='█', print_end='\r'):
    """
    Progress bar.
    """
    percent = 100 * (iteration / total)
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    elapsed_time = time.time() - start_time
    print(f'\r{prefix} |{bar}| {percent:.1f}% Elapsed: {elapsed_time:.1f}s', end=print_end)
    if iteration == total:
        print()

#----------------------------------------
# Protocol execution
#----------------------------------------
if __name__=='__main__':

    key_length = int(sys.argv[1])
    num_iter = int(sys.argv[2])
    pbit = float(sys.argv[3])  # Probability for bit-flip
    pphase = float(sys.argv[4])  # Probability for phase-flip
    sim = AerSimulator()
    attack = bool(sys.argv[5])
    percentages = []

    start_time = time.time()

    b = quantum_random_binary_string(key_length)
    a = quantum_random_binary_string(key_length)
    if attack:
        print('--- Simulations with attacker ---\n')
        a_xor_b = tuple(i ^ j for i, j in zip(a, b))

    iter=1
    for i in range(num_iter):
        dec = random.choice([0, 1])
        # 1. Keys generation (this keys could be shared through QKD)

        # 2. Preparation of the challenge (Bob)
        psi = psi_gen(a, b) # |psi> state generation from a and b

        c = quantum_random_binary_string(key_length) # Random generation for c
        challenge_state = challenge_gen(psi, c, b) # Challenge setup

        # After this, Bob sends the modified qubits to Alice 

        if dec == 0:
            # Honest prover Alice

            # 3.  Alice modification's

            proof_state = alice_mod(challenge_state, a, b)

            # Alice send the proof state to Bob.

            # 6. Bob retrieves c.
            b_xor_c = measurements(proof_state, a)
            c_aprox = tuple(i ^j for i,j in zip(b, b_xor_c))
            equal_percentage = equal_entries_percentage(c, c_aprox)
            percentages.append((equal_percentage, dec))

        else:
            if attack == True:
                # 3. Eve (which has access to a XOR b) meassures the challenge state randomly and generates the attakc estimation
                r = random_binary_string(key_length)
                measure_results = measurements(challenge_state, r)
                attack_estimation = tuple(i ^ j for i,j in zip(a_xor_b, measure_results))
        
                # 4. Eve generates the attack state encoding the attack estimaiton with ranodm bassis
                r = random_binary_string(key_length)
                attack_state = psi_gen(attack_estimation, r)
                # 5. Eve sends the attack state to Bob and he measures and count matches
                results = measurements(attack_state, a)
                c_aprox = tuple(i ^j for i,j in zip(b, results))
                equal_percentage = equal_entries_percentage(c, c_aprox)
                percentages.append((equal_percentage, dec))
            else:
                # Dishonest prover Eve
                c_aprox = random_binary_string(key_length)
                equal_percentage = equal_entries_percentage(c, c_aprox)
                percentages.append((equal_percentage, dec))
        loading_bar(iter, num_iter, start_time)
        iter +=1

    #----------------------------------------
    # Data
    #----------------------------------------
    equal_percentages = [x[0] for x in percentages]
    decisions = [x[1] for x in percentages]

    iters = range(1,num_iter + 1)
    results = pd.DataFrame({'Iteration': iters, 'Decision': decisions, 'Percentages': equal_percentages})
    results.to_csv(f'iter_flip_error_data_attack={attack}_{key_length}_{num_iter}.csv', index=False)
