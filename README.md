# PRESSURIZED PIPE NETWORK OPTIMIZER (PPNO)

2019-2026 - Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/

## VERSION 0.3.1
Modernized and refactored version with improved nomenclature and Pythonic standards.

---

## INSTALLATION

It is highly recommended to install `pygmo` using Conda before installing `ppno`:

```powershell
conda install -c conda-forge pygmo
pip install .
```

## DEPENDENCIES
Requires (specified in `setup.py`):
- `numpy`
- `SciPy`
- `PyGMO`
- `pytest` (for development)

---

## PURPOSE
The program optimizes the pipe diameters of a pressure pipe network defined by an EPANET 2.x model. The result is the selection of the most cost-effective pipe diameters from a catalog that meet the minimum pressure requirements at specified nodes.

---

## RUN
You can run the optimizer directly using the installed entry point or by executing the module:
```powershell
ppno problem.ext
```
Where `problem.ext` is the problem definition file.

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
PVC  125.0    0.100     1.56
PVC  150.0    0.100     1.75
```

---

## RESULTS
The optimized results are displayed in the console and a new EPANET file is generated. The filename includes a suffix based on the algorithm used: `_Solved_UH`, `_Solved_DE`, etc.

If refinement was enabled, an additional `+Refinement` indicator is added.

---

## EXAMPLES
Sample problems are available in the `ppno/examples/` directory.

---

