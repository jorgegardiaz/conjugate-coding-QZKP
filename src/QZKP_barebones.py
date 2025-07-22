from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import sys

#----------------------------------------
# Funcitons
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
        raise ValueError('Same number of basis and bits expected.')
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

def alice_mod(psi, a, b):
    if len(psi) != len(a) or len(psi) != len(a):
        raise ValueError('Same number of qubits and bits expected.')
    a_xor_b = tuple(i ^ j for i,j in zip(a,b))
    for i in range(len(psi)):
        if b[i] == 1:
            psi[i].z(0)
        if a_xor_b[i] == 1:
            psi[i].h(0)
        if a[i] == 1:
            psi[i].z(0)
    return psi

def measurements(psi, basis):
    if len(psi) != len(basis):
        raise ValueError('Same number of qubits and basis expected.')
    results = []
    for i in range(len(psi)):
        if basis[i] == 1:
            psi[i].h(0)
        psi[i].measure(0, 0)
        exec = sim.run(psi[i], shots=1).result()
        result = int(list(exec.get_counts(psi[i]).keys())[0])
        results.append(result)
    return results

def equal_entries_percentage(list1, list2):
    if len(list1) != len(list2):
        raise ValueError("The lists must have the same length.")
    equals = 0
    for (a, b) in zip(list1, list2):
        equals += int(a == b)
    return (equals / len(list1)) * 100

#----------------------------------------
# Protocol execution
#----------------------------------------
if __name__ == '__main__':
    
    sim = AerSimulator()
    key_length = int(sys.argv[1])
    b = tuple(quantum_random_binary_string(key_length))
    a = tuple(quantum_random_binary_string(key_length))
    verbose = False
    if len(sys.argv) == 3:
        if str(sys.argv[2]) == 'v':
            verbose = True

    # 2. Preparation of the challenge (Bob)
    psi = psi_gen(a, b) # |psi> state generation from a and b

    c = tuple(quantum_random_binary_string(key_length)) # Random generation for c
    challenge_state = challenge_gen(psi, c, b) # Challenge setup

    # After this, Bob sends the modified qubits to Alice 

    # 3.  Alice modification's

    proof_state = alice_mod(challenge_state, a, b)

    # Alice send the proof state to Bob.

    # 6. Bob retrieves c.
    b_xor_c = measurements(proof_state, a)
    c_aprox = tuple(i ^j for i,j in zip(b, b_xor_c))
    equal_percentage = equal_entries_percentage(c, c_aprox)

    if verbose:

        print('\n--- Random Shared Secret Keys ---')
        print(f'Secret bits ---> a = {a}')
        print(f'Secret basis ---> b = {b}\n')
        secret_state =  [a_val if b_val == 0 else ('+' if a_val == 0 else '-') for a_val, b_val in zip(a, b)]
        print(f'Coded secret state ---> {tuple(secret_state)}\n')
        
        
        print(f'--- Challenge Generation ---')
        challenge_state = [s_val if c_val == 0 else ({0: 1, 1: 0, '+': '-', '-': '+'}[s_val]) for s_val, c_val in zip(secret_state, c)]
        print(f'Random challenge sequence ---> c = {c}')
        print(f'Challenge state ---> {tuple(challenge_state)}')
        

        print('\n\n--- Bob sends challenge State through Quantum Channel to Alice --- \n\n')

        print('--- Alice\'s Modifications and Proof State Generation ---')
        proof_state =  [a_val if b_val == 0 else ('+' if a_val == 0 else '-') for a_val, b_val in zip(b_xor_c, a)]
        print(f'Proof state ---> {tuple(proof_state)}')
        

        print('\n\n--- Alice sends the proof state to Bob ---\n\n')

        print('--- Bob recovers c ---')
        print(f'Measurement results ---> {tuple(b_xor_c)}')
        print(f'Recovered c ---> {c_aprox}')
        print(f'Number of coincidences ---> {int(equal_percentage*key_length/100)}')

    print(f'\n{equal_percentage}% accuracy for {key_length} bits keys length.\n')
