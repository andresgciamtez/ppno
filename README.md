# PRESSURIZED PIPE NETWORK OPTIMIZER (PPNO)

2019-2026 - Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/

## VERSION 0.3.1
Modernized and refactored version with improved nomenclature and Pythonic standards.

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
- `numpy`
- `SciPy`
- `PyGMO`
- `entoolkit` (EPANET 2.2 Wrapper)

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
ppno ppno/examples/Example1.ext
```

### What happens during a run?
1. **Validation**: PPNO parses your `.ext` file and loads the associated EPANET `.inp` network.
2. **Optimization**: The selected algorithm searches for the best diameters to minimize cost while satisfying pressure constraints.
3. **Execution**: Real-time progress is shown in the console.
4. **Completion**: A final summary table is printed, and a new optimized EPANET `.inp` file is saved to disk.

---

## PROBLEM DEFINITION
The input file uses a structure similar to an EPANET `.inp` file, with a `.ext` extension. Sections are indicated by header labels (`[]`).

### [TITLE]
Optional description of the problem.
Example:
```ini
[TITLE]
Hanoi example by Fujiwara and Khang, 1990
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
- **Algorithm**: The optimization method to use:
    - `UH`: **Unit Headloss Heuristic**. Simple and fast heuristic that increases diameters based on maximum headloss.
    - `DE`: **Differential Evolution**. Robust global optimization from SciPy.
    - `DA`: **Dual Annealing**. Efficient global optimization for large spaces.
    - `NSGA2`: **Non-dominated Sorting Genetic Algorithm II**. Multi-objective approach via PyGMO.
    - `SHGO`: **Simplicial Homology Global Optimization**. Deterministic algorithm, useful for constrained problems.
    - `DIRECT`: **DIviding RECTangles**. Robust deterministic search algorithm.
- **Refinement**: `YES` or `NO`. Enables a final greedy refinement to further reduce costs in non-critical pipes.

Example:
```ini
[OPTIONS]
Algorithm UH
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
