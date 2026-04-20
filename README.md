# PRESSURIZED PIPE NETWORK OPTIMIZER (PPNO)

2019-2026 - Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/

## VERSION 0.3.1
Modernized version with multi-algorithm support, automatic retries, and enhanced EPANET 2.2 integration.

---

## 🛠 INSTALLATION

The most reliable way to install **PPNO** is using [Conda](https://docs.conda.io/en/latest/miniconda.html) to manage the complex scientific dependencies (especially `PyGMO`).

### Step-by-Step Setup

1. **Create and activate a dedicated environment:**
   ```powershell
   conda create -n ppno python=3.9
   conda activate ppno
   ```

2. **Install binary dependencies via conda-forge:**
   > [!IMPORTANT]
   > We strongly recommend installing `pygmo` via Conda to avoid common compilation issues with `pip`.
   ```powershell
   conda install -c conda-forge numpy scipy pygmo
   ```

3. **Install the EPANET Toolkit wrapper (entoolkit):**
   PPNO now relies on the external `entoolkit` library. Install it from your local repository:
   ```powershell
   # Adjust path as necessary
   pip install ../entoolkit/entoolkit
   ```

4. **Install PPNO from the local source directory:**
   Navigate to the project root and run:
   ```powershell
   pip install .
   ```

---

## DEPENDENCIES
- [numpy](https://numpy.org/)
- [SciPy](https://scipy.org/)
- [PyGMO](https://esa.github.io/pygmo2/)
- [entoolkit](https://github.com/andresgciamtez/entoolkit) (EPANET 2.2 Wrapper)

---

## PURPOSE
The program optimizes the pipe diameters of a pressure pipe network defined by an EPANET 2.x model. The result is the selection of the most cost-effective pipe diameters from a catalog that meet the minimum pressure requirements at specified nodes.

---

## 🚀 RUN

PPNO is easy to use from the command line once installed.

### Basic Syntax
```powershell
ppno <problem_file.ext>
```

### Try an Example
You can test the installation using one of the provided example problems:
```powershell
ppno ppno/examples/example_1.ext
```

### What happens during a run?
1. **Validation**: PPNO parses your `.ext` file and loads the associated EPANET `.inp` network.
2. **Optimization**: The selected algorithm searches for the best diameters to minimize cost while satisfying pressure constraints.
3. **Execution**: Real-time progress is shown in the console.
4. **Completion**: A final **ALGORITHM SUMMARY** table is printed, showing the performance (time, simulations, success, cost) of each run, and the best optimized EPANET `.inp` file is saved to disk.

---

## PROBLEM DEFINITION
The input file uses a structure similar to an EPANET `.inp` file, with a `.ext` extension. Sections are indicated by header labels (`[]`).

### [TITLE]
Optional description of the problem.
Example:
```ini
[TITLE]
Optimization of the Hanoi Network (Fujiwara & Khang, 1990)
```

### [INP]
Path to the EPANET input file (`.inp`).
Example:
```ini
[INP]
networks/hanoi.inp
```

### [OPTIONS]
Calculation options.
- **Algorithm**: The optimization method(s) to use. You can specify a single algorithm or a space-separated list of multiple algorithms to run in sequence.
    - `UH`: **Unit Headloss Heuristic**. Simple and fast heuristic that increases diameters based on maximum headloss (Internal).
    - `DE`: **Differential Evolution**. Robust global optimization from **SciPy**.
    - `DA`: **Dual Annealing**. Efficient global optimization for large spaces from **SciPy**.
    - `SHGO`: **Simplicial Homology Global Optimization**. Deterministic algorithm, useful for constrained problems from **SciPy**.
    - `DIRECT`: **DIviding RECTangles**. Robust deterministic search algorithm from **SciPy**.
    - `NSGA2`: **Non-dominated Sorting Genetic Algorithm II**. Multi-objective approach via **PyGMO**.
    - `MOEAD`: **Multi-Objective Evolutionary Algorithm based on Decomposition**. Advanced multi-objective solver via **PyGMO**.
    - `MACO`: **Multi-Objective Ant Colony Optimization**. Nature-inspired algorithm perfect for discrete network paths via **PyGMO**.
    - `PSO`: **Particle Swarm Optimization (NSPSO)**. Fast non-dominated sorting particle swarm optimizer via **PyGMO**.
- **MaxRetries**: (Optional) Number of times to retry an algorithm if it fails to find a feasible solution. Default is 3.
- **Refinement**: `YES` or `NO`. Enables a final greedy refinement to further reduce costs in non-critical pipes.

Example:
```ini
[OPTIONS]
Algorithm DE DA UH
MaxRetries 2
Refinement YES
```

### [PIPES]
Pipes to be sized, followed by the name of the pipe series from the catalog.
Example:
```ini
[PIPES]
P1    PVC
P2    PVC
P3    STAINLESS_STEEL
```

### [PRESSURES]
Minimum pressure constraints for specific nodes.
Example:
```ini
[PRESSURES]
N2    20.0
N4    20.0
```

### [CATALOG]
Defines the available pipe series. Each line contains:
`Series Name | Diameter | Roughness | Unit Cost`
Example:
```ini
[CATALOG]
PVC  90.0    0.100     1.00
PVC  125.0   0.100     1.56
PVC  150.0   0.100     1.75
```

---

## RESULTS
The optimized results are displayed in the console and a new EPANET file is generated. The filename includes a suffix based on the algorithm used: `_Solved_UH`, `_Solved_DE`, etc.

---

## EXAMPLES
Sample problems are available in the `ppno/examples/` directory.

---

## 📜 LICENSE & CITATION

### License
PPNO is licensed under the **Apache License 2.0**. You are free to use, modify, and distribute this software, provided you include the original copyright notice and a copy of the license.

### Citation
If you use PPNO in your research or professional projects, please cite it as follows:

> García Martínez, A. (2019-2026). *PPNO: Pressurized Pipe Network Optimizer*. GitHub repository: [https://github.com/andresgciamtez/ppno](https://github.com/andresgciamtez/ppno)

---

## 🙏 ACKNOWLEDGMENTS

- **[EPANET](https://www.epa.gov/water-research/epanet)**: Developed by the US EPA, the hydraulic engine of this tool.
- **[Pagmo/PyGMO](https://esa.github.io/pygmo2/)**: For the powerful parallel optimization algorithms.
- **SciPy Community**: For the robust implementation of global optimization methods.
- **[entoolkit](https://github.com/andresgciamtez/entoolkit)**: For providing the modern Pythonic wrapper for EPANET 2.2.

---

2019-2026
