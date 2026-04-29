# PRESSURIZED PIPE NETWORK OPTIMIZER (PPNO)

2019–2026 – Andrés García Martínez
Licensed under the Apache License 2.0
http://www.apache.org/licenses/

📌 What is PPNO?

PPNO is a command-line tool for the cost-optimal design of pressurized water distribution networks, built on top of the EPANET hydraulic simulation engine.

It solves the classical engineering problem of pipe diameter optimization under hydraulic constraints, where trade-offs between cost and pressure feasibility must be balanced. This problem has been widely studied using evolutionary and hybrid optimization techniques coupled with EPANET-based simulation .

PPNO introduces a hybrid two-stage optimization pipeline that combines:

Deterministic heuristics (fast feasibility)
Hydraulically-informed local search (FLS-H)
Optional global metaheuristics (e.g., DE, NSGA-II)
🚀 Key Features
Two-stage hybrid optimization pipeline
Hydraulically-aware local search (FLS-H)
Metaheuristic seeding with feasible solutions
Global evaluation cache (EPANET call reduction)
Incremental result export in .scn format
Robust parsing and validation
Designed for reproducibility and batch execution
🛠️ Installation

Install from source:

pip install .

Recommended (development mode):

pip install -e .
⚠️ Windows Troubleshooting

If ppno is not recognized:

[System.Environment]::SetEnvironmentVariable(
  "Path",
  $env:Path + ";<PathToYourPythonEnv>\Scripts",
  "User"
)

Or run:

python -m ppno.ppno <problem_file.ext>
📖 Basic Usage

Run the optimizer with:

ppno problem_definition.ext
Execution Flow
Load EPANET model from [INP]
Run Stage 1 (mandatory)
Optionally run Stage 2 metaheuristics
Export results as .scn files
📁 Outputs

PPNO generates lightweight, reusable solution files:

<original_inp_name>_result_<algorithm>.scn
Contents

A standard EPANET [PIPES] section:

Pipe ID
Optimized diameter
Roughness coefficient
Why .scn?
Avoids duplicating full .inp models
Enables modular post-processing pipelines
Supports versioning and comparison of solutions
Seamless reintegration into existing EPANET workflows
⚙️ Optimization Pipeline

PPNO uses a coordinated two-stage architecture:

Stage 1 (Mandatory)
    UH → FLS-H → Feasible solution x₁

Stage 2 (Optional)
    Seed(x₁) → Metaheuristics → FLS-H → Final solution
1️⃣ Stage 1 — Heuristic Foundation & Refinement

Builds a high-quality feasible baseline:

Unit Headloss Heuristic (UH)
Rapidly generates a feasible diameter configuration
FLS-H Refinement
Improves cost while preserving feasibility

➡️ Output:
A feasible solution x₁, used as the anchor for global search

2️⃣ Stage 2 — Global Exploration (Optional)

Enhances the baseline using metaheuristics:

Population Injection
x₁ is inserted into the initial population
Feasible Variants
Perturbed versions of x₁ are generated and repaired
Final Local Polish (FLS-H)
Ensures no local improvements are missed
Supported Algorithms
Differential Evolution (DE)
Dragonfly Algorithm (DA)
NSGA-II
MOEA/D
MACO
PSO
🧠 FLS-H: Feasible Local Search – Hybrid

FLS-H is the core optimization engine of PPNO.

It is a hydraulically-informed local search algorithm designed to:

Preserve feasibility at all times
Minimize expensive EPANET evaluations
Exploit network structure for efficient cost reduction
Key Mechanisms
Feature	Description
Global Evaluation Cache	Avoids repeated EPANET simulations via hashing
Hydraulic Awareness	Targets pipes with high gradient impact
Fast Constraints	Filters invalid candidates before simulation
Stochastic Worsening	Escapes local minima with controlled cost increases
⚙️ Configuration (.ext file)

Example:

[OPTIONS]

; --- Local Search ---
RefinerIters 50
RefinerNeighbors 20
RefinerWorsening 0.01

; --- Stage 2 ---
Algorithm NSGA2 DE
MaxRetries 3
MaxTime 120
RandomSeed 42

; --- PyGMO ---
PopulationSize 100
Generations 100
Patience 10
MaxTrials 250
🧪 Design Philosophy

PPNO is built around three core principles:

1. Feasibility First

Solutions are always hydraulically valid before optimization continues.

2. Hybrid Optimization

Combines:

deterministic heuristics
local search
global metaheuristics
3. Simulation as Oracle

EPANET is treated as the ground-truth evaluator, ensuring engineering realism.

🛡️ Robustness & Validation
Semantic validation of inputs
Detection of:
missing files
invalid topology
catalog inconsistencies
Graceful failure (exit code 1)
Multi-encoding support (UTF-8, UTF-16, CP1252)
High test coverage (~90%+)
📌 Use Cases

PPNO is suitable for:

✔️ Design of new water distribution networks
✔️ Rehabilitation and pipe replacement planning
✔️ Cost optimization studies
✔️ Academic research and benchmarking
✔️ Scenario analysis and sensitivity studies
📜 License & Citation

Apache License 2.0

If you use PPNO in research:

García Martínez, A. (2019–2026).
PPNO: Pressurized Pipe Network Optimizer
https://github.com/andresgciamtez/ppno
