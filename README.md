# PRESSURIZED PIPE NETWORK OPTIMIZER (PPNO)

2019-2026 - Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/

## VERSION 0.3.2
Modernized version featuring a structural 3-stage optimization engine with **FLS-H** local search and advanced metaheuristic population seeding.

---

## 🚀 THE TWO-STAGE OPTIMIZATION PIPELINE

PPNO has moved away from isolated algorithm execution to a coordinated **2-stage pipeline**. This approach ensures that global metaheuristics don't waste time exploring infeasible or low-quality regions of the search space.

### 1. Stage 1: Heuristic Foundation & Initial Refinement (Mandatory)
The process always starts by building a feasible baseline:
-   **Unit Headloss Heuristic (UH)**: Rapidly finds an initial set of diameters that satisfy pressure constraints.
-   **FLS-H Refinement**: After UH, the **Feasible Local Search – Hybrid** algorithm performs an initial "sharpening" to reduce investment costs while maintaining feasibility.
-   **Result**: A high-quality, feasible solution $x_1$ that serves as the anchor for the rest of the pipeline.

### 2. Stage 2: Global Exploration via Hybrid Seeding (Optional)
If stage 2 metaheuristics (Genetics, DE, etc.) are configured, they perform a global search using an advanced **Seeding Strategy**:
-   **Population Injection**: Instead of starting with a random population, the solver injects $x_1$ into the starting set.
-   **Feasible Variation**: A portion of the initial population is filled with "feasible variants" of $x_1$ (random perturbations that are automatically repaired).
-   **Final Polish**: After the metaheuristic completes, a final pass of the **FLS-H** algorithm is applied to the best global solution found. This ensures that even minor cost-reduction opportunities often missed by global metaheuristics are captured.
-   **Benefits**: By starting "on the shoulders" of a feasible local optimum, global solvers converge significantly faster and focus on finding global improvements rather than struggling with basic feasibility.
-   **Supported Solvers**: `DE`, `DA`, `NSGA2`, `MOEAD`, `MACO`, `PSO`.



## 📜 FLS-H (Feasible Local Search – Hybrid)

The hardware of this new pipeline is the **FLS-H** module. It is a local search algorithm specialized for hydraulic networks:

| Feature | Description |
| :--- | :--- |
| **Global Evaluation Cache** | Avoids redundant EPANET simulations by hashing and storing evaluation results across the entire session. |
| **Hydraulic Rules** | Neighborhood generation targets pipes with high hydraulic potential (gradient) for more efficient cost reduction. |
| **Fast Constraints** | Filters out obviously invalid solutions (bounds, connectivity) without calling the EPANET engine. |
| **Stochastic Worsening** | Occasionally accepts small cost increases (<1-2%) to jump out of narrow local minima. |

---

## ⚙️ CONFIGURATION ([OPTIONS])

The `.ext` file controls the optional Stage 2 of the pipeline. Example:

```ini
[OPTIONS]
Algorithm DE DA NSGA2
MaxRetries 3
```

-   **Algorithm**: A space-separated list of metaheuristics (DE, DA, DIRECT, NSGA2, MOEAD, MACO, PSO).
    -   Example: `Algorithm NSGA2 DE` (Runs both Stage 2 algorithms sequentially).
    -   Example: `; Algorithm` (Skips Stage 2, running only mandatory Stage 1 + 3).
-   **MaxRetries**: Retries for Stage 2 algorithms if they fail to improve the baseline.
-   **Report**: Set to `YES` to automatically generate EPANET `.rpt` files upon success.

---

## 🛡️ ROBUSTNESS & VALIDATION

PPNO features a defensive programming architecture:
- **Semantic Validation**: Automatically checks for missing files, invalid sections, orphaned nodes/pipes, and anomalies in the catalog (e.g., non-monotonic diameters, anomalous pricing).
- **Graceful Failure**: Exits with code `1` on fatal errors, making it safe for CI/CD pipelines and batch scripts.
- **Resilient Parsing**: Supports UTF-8, UTF-16, and CP1252 encodings gracefully.
- **Test Coverage**: The optimization engine and parser are backed by an exhaustive test suite targeting high branch coverage (~90%+).

---

## 📜 LICENSE & CITATION

**Apache License 2.0**.
If you use PPNO in your research, please cite:
> García Martínez, A. (2019-2026). *PPNO: Pressurized Pipe Network Optimizer*. GitHub repository: [https://github.com/andresgciamtez/ppno](https://github.com/andresgciamtez/ppno)

---

2019-2026
