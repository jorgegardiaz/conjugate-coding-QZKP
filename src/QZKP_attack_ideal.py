from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import random
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import time
import sys


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
            else:
                psi[i].z(0)
    return psi

def zk_mod(psi, p):
    '''
    Alice Zero-Knowledge momdifications to the state |psi>.
    '''
    if len(psi) != len(p):
        raise ValueError('Same number of qubits and bits expected.')
    for i in range(len(psi)):
        if p[i] == 1:
            psi[i].h(0)
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
        psi[i].measure(0, 0)
        exec = sim.run(psi[i], shots=1).result()
        result = int(list(exec.get_counts(psi[i]).keys())[0])
        results.append(result)
    return results

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
    sim = AerSimulator()
    
    percentages = []

    start_time = time.time()

    b = quantum_random_binary_string(key_length)
    a = quantum_random_binary_string(key_length)

    a_xor_b = tuple(i ^ j for i,j in zip(a,b))

    iter=1
    for i in range(num_iter):
    
        # 2. Preparation of the challenge (Bob)
        psi = psi_gen(a, b) # |psi> state generation from a and b

        c = tuple(quantum_random_binary_string(key_length)) # Random generation for c
        challenge_state = challenge_gen(psi, c, b) # Challenge setup

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
        percentages.append(equal_percentage)
        loading_bar(iter, num_iter, start_time)
        iter +=1

    #----------------------------------------
    # Data
    #----------------------------------------
    iters = range(1,num_iter + 1)
    results = pd.DataFrame({'Iteration': iters, 'Percentages': percentages})
    results.to_csv(f'iter_attack_data_{key_length}_{num_iter}.csv', index=False)
