# PRESSURIZED PIPE NETWORK OPTIMIZER (PPNO)

2019-2026 - Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/

## VERSION 0.3.5
Modernized version featuring a structural 3-stage optimization engine with **FLS-H** local search and advanced metaheuristic population seeding.

---

## 🚀 THE THREE-STAGE OPTIMIZATION PIPELINE

PPNO has moved away from isolated algorithm execution to a coordinated **3-stage pipeline**. This approach ensures that global metaheuristics don't waste time exploring infeasible or low-quality regions of the search space.

### 1. Stage 1: Heuristic Foundation & Initial Refinement (Mandatory)
The process always starts by building a feasible baseline:
-   **Unit Headloss Heuristic (UH)**: Rapidly finds an initial set of diameters that satisfy pressure constraints.
-   **FLS-H Refinement**: After UH, the **Feasible Local Search – Hybrid** algorithm performs an initial "sharpening" to reduce investment costs while maintaining feasibility.
-   **Result**: A high-quality, feasible solution $x_1$ that serves as the anchor for the rest of the pipeline.

### 2. Stage 2: Global Exploration via Hybrid Seeding (Optional)
If stage 2 metaheuristics (Genetics, DE, etc.) are configured, they perform a global search using an advanced **Seeding Strategy**:
-   **Population Injection**: Instead of starting with a random population, the solver injects $x_1$ into the starting set.
-   **Feasible Variation**: A portion of the initial population is filled with "feasible variants" of $x_1$ (random perturbations that are automatically repaired).
-   **Benefits**: By starting "on the shoulders" of a feasible local optimum, global solvers converge significantly faster and focus on finding global improvements rather than struggling with basic feasibility.
-   **Supported Solvers**: `DE`, `DA`, `NSGA2`, `MOEAD`, `MACO`, `PSO`.

### 3. Stage 3: Mandatory Polish for Global Search (Conditional)
This stage only executes if **Stage 2** was performed. It applies a final pass of the **FLS-H** algorithm to the best global solution found. This ensures that even minor cost-reduction opportunities often missed by global metaheuristics are captured, delivering the absolute minimum cost possible.

---

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

The `.ext` file controls the optional Stage 2 of the pipeline:

-   **Algorithm**: A space-separated list of metaheuristics.
    -   Example: `Algorithm NSGA2 DE` (Runs both Stage 2 algorithms sequentially).
    -   Example: `; Algorithm` (Skips Stage 2, running only mandatory Stage 1 + 3).
-   **MaxRetries**: Retries for Stage 2 algorithms if they fail to improve the baseline.
-   **Refinement**: (Legacy) This is now `YES` by default as it powers Stage 1 and 3.

```ini
[OPTIONS]
Algorithm DE DA NSGA2
MaxRetries 3
```

---

## 📜 LICENSE & CITATION

**Apache License 2.0**.
If you use PPNO in your research, please cite:
> García Martínez, A. (2019-2026). *PPNO: Pressurized Pipe Network Optimizer*. GitHub repository: [https://github.com/andresgciamtez/ppno](https://github.com/andresgciamtez/ppno)

---

2019-2026
