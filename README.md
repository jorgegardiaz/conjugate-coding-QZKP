# Desiganted Verifyer Quantum Perfect Zero Knowledge Proof based on Conjugate Coding

This repository contains an implementation of a **zero knowledge** cryptographic protocol in a quantum setting, using libraries such as [Qiskit](https://qiskit.org/). The main goal is to demonstrate how to validate information (e.g., a secret bitstring and its basis) without revealing this secret itself, by leveraging quantum states.

## Table of Contents
- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Script Usage](#script-usage)
  - [1. QZKP_barebones.py](#1-qzkp_barebonespy)
  - [2. QZKP_attack_ideal.py](#2-qzkp_idealpy)
  - [3. QZKP_noise_damping.py](#3-qzkp_noise_dampingpy)
  - [4. QZKP_noise_flip.py](#4-qzkp_noise_flippy)
- [Graphical User Interface (GUI)](#GUI)
- [Contributions](#contributions)
- [License](#license)

---

## Overview

This project explores a **Zero Knowledge Proof (ZKP)** approach within the quantum paradigm (QZKP, Quantum Zero Knowledge Proof). It leverages quantum states to prove the possession of certain information (like a secret bitstring and the basis in which it was encoded) without revealing the actual secret to the verifier.

The repository includes different scripts that illustrate various versions of the protocol:

- **Basic version** without noise.
- **Versions with different noise models** (phase damping, bit-flip, phase-flip).
- **A minimal example** to showcase the fundamental steps of the protocol.

---

## Repository Structure

```bash
├── README.md
├── requirements.txt
├── src
│   ├── QZKP_GUI.py
│   ├── QZKP_barebones.py
│   ├── QZKP_attack_ideal.py
│   ├── QZKP_noise_damping.py
│   ├── QZKP_noise_flip.py
```
---

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Qiskit](https://qiskit.org/) (including `qiskit-aer`)
- [matplotlib](https://matplotlib.org/)
- [pandas](https://pandas.pydata.org/)
- [numpy](https://numpy.org/)
- [wxPython](https://wxpython.org/)
- [openpyxl](https://openpyxl.readthedocs.io/en/stable/)

All dependencies are listed in the `requirements.txt` file with their corresponding compatible version.

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/jorgegardiaz/conjugate_coding_QZKP.git
   cd conjugate_coding_QZKP
   ```
2. *(Optional)* **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Linux/Mac
   venv\Scripts\activate   # For Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Script Usage

### 1. `QZKP_barebones.py`
A **minimal** script that shows the fundamental protocol steps:
```bash
python QZKP_barebones.py <key_length> <verbose>
```
It prints the percentage of correctly guessed challenge bits (the “success rate”) for a given key length.

If verbose option is selected (\<verbose\> == v) it will print all binary sequences and quantum states step by step, this paremeter is opcional. 

### 2. `QZKP_attack_ideal.py`
An **ideal** version (no noise) that simulates *dishonest* prover one (Eve) wich has access to $a\oplus b$:
```bash
python QZKP_ideal.py <key_length> <num_iterations>
```
Generates CSV files with statistics for the success rate of each iteration.

### 3. `QZKP_noise_damping.py`
Implements a **phase-amplitude damping** noise model:
```bash
python QZKP_noise_damping.py <key_length> <num_iterations> <gamma> <lambda> <attacker>
```
Saves CSVs with results for honest and dishonest prover outcomes under damping noise.

### 4. `QZKP_noise_flip.py`
Implements **bit-flip** and **phase-flip** noise models:
```bash
python QZKP_noise_flip.py <key_length> <num_iterations> <pbit> <pphase> <attacker>
```
Similar data output to the other scripts, generating CSVs with per-iteration metrics.

---
# Graphical User Interface (GUI)

This project includes a user-friendly graphical interface built with wxPython that acts as a launcher and visualizer for all the simulation scripts.

### How to Run
To start the application, run the `QZKP_GUI.py` script from the root directory of the project:
```bash
python src/QZKP_GUI.py
```

### Features
The GUI provides a centralized and interactive way to run the simulations:

- **Simulation Selection:** A dropdown menu allows you to choose which of the four protocols to run.

- **Interactive Parameters:** The interface dynamically displays the necessary parameters for the selected script (key length, iterations, noise levels, etc.), which can be adjusted easily.

- **Real-time Progress:** For long-running simulations, a progress bar, a percentage counter, and an elapsed time stopwatch provide real-time feedback on the execution status.

- **Results Visualization:** For iterative simulations, a scatter plot is automatically generated upon completion, showing the success rate per iteration and distinguishing between honest and dishonest runs.

- **Data and Plot Export:** A dedicated "Save" section appears for iterative simulations, allowing you to:

   - Save the plot in various formats, including PNG, PDF, and SVG.

   - Save the raw simulation data to CSV, JSON, or Excel (.xlsx) files for further analysis.

- **Console Output:** For the "Basic Protocol", the output view automatically switches to a text console to display the detailed step-by-step verbose output, which can also be saved to a `.txt` file.
---

## Contributions
Contributions are welcome! To propose changes:
1. Fork this repository
2. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/new-functionality
   ```
3. Commit your changes:
   ```bash
   git commit -m 'Add new functionality or fix bug XYZ'
   ```
4. Submit a Pull Request and describe the changes in detail.

---

## License
This project is available under the MIT License. See the file [LICENSE](LICENSE) for more information.
