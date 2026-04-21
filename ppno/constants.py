"""Global constants and algorithm IDs for PPNO."""

# Algorithm IDs mapped to numerical constants for internal tracking
ALGORITHM_UH = 0       # Unit Headloss Heuristic
ALGORITHM_DE = 1       # SciPy: Differential Evolution
ALGORITHM_DA = 2       # SciPy: Dual Annealing
ALGORITHM_NSGA2 = 3    # PyGMO: Non-dominated Sorting Genetic Algorithm II
ALGORITHM_DIRECT = 4   # SciPy: DIRECT algorithm
ALGORITHM_MOEAD = 5    # PyGMO: Multi-Objective Evolutionary Algorithm based on Decomposition
ALGORITHM_MACO = 6     # PyGMO: Multi-objective Ant Colony Optimizer
ALGORITHM_PSO = 7      # PyGMO: Non-dominated Sorting Particle Swarm Optimizer

# Global Optimization Parameters
PENALTY_VALUE = 1e9          # Base penalty added to infeasible solutions in SciPy
MAX_RETRIES = 3              # Default number of retries if an algorithm fails to improve the baseline
MAX_ALGORITHM_TIME = 120    # Maximum time (in seconds) allowed per algorithm execution

# Local Search (FLS-H) Settings
LS_MAX_ITER = 50                 # Maximum iterations for the refinement loop
LS_ACCEPTANCE_THRESHOLD = 0.01   # Percentage (0.01 = 1%) of allowed cost worsening to escape local minima
LS_NEIGHBORHOOD_SIZE = 20        # Number of mutated candidate solutions generated per iteration
