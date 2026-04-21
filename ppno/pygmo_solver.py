"""Optimization module using various algorithms via PyGMO.

This module adapts the PPNO problem to the PyGMO framework for multi-objective
optimization, supporting algorithms like NSGA-II, MOEAD, MACO, and PSO.
"""

import logging
from time import perf_counter
from typing import Tuple, Optional, List, Any

import numpy as np
import pygmo as pg
from .constants import MAX_ALGORITHM_TIME

# Logger configuration
logger = logging.getLogger(__name__)

# Default Evolution Parameters
GENERATIONS_PER_TRIAL = 100
POPULATION_SIZE = 100
MAX_TRIALS = 250
MAX_NO_CHANGES = 10



class PPNOProblem:
    """User-Defined Problem (UDP) for PyGMO integration.

    Adapts the network optimization problem to a format compatible with PyGMO
    algorithms, defining objectives, bounds, and variable types.

    Attributes:
        optimization_instance (Any): The main Optimization object.
    """

    def __init__(self, optimization_instance: Any):
        """Initializes the problem adapter.

        Args:
            optimization_instance: An instance of the Optimization class.
        """
        self.optimization_instance = optimization_instance

    def fitness(self, x: np.ndarray) -> List[float]:
        """Calculates fitness values for a given solution vector.

        Objectives:
            1. Total network cost (to be minimized).
            2. Maximum pressure deficit (to be minimized towards <= 0).

        Args:
            x: Vector of diameter indexes.

        Returns:
            List containing [cost, max_deficit].
        """
        diameter_indexes = x.astype(np.int32)
        self.optimization_instance.set_x(diameter_indexes)

        # Objective 1: Investment Cost
        cost = float(self.optimization_instance.get_cost())

        # Objective 2: Feasibility (Pressure Deficit)
        # We look for the maximum deficit across all nodes.
        # A value <= 0 means all nodes satisfy pressure requirements.
        nodal_deficits = self.optimization_instance.check(mode='PD')
        max_deficit = float(np.max(nodal_deficits))

        return [cost, max_deficit]

    def get_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        """Returns the lower and upper bounds for each variable."""
        return self.optimization_instance.lbound, self.optimization_instance.ubound

    def get_nobj(self) -> int:
        """Returns the number of objectives (Cost and Max Deficit)."""
        return 2

    def get_nix(self) -> int:
        """Returns the number of integer variables."""
        return self.optimization_instance.dimension

    def get_name(self) -> str:
        """Returns the descriptive name of the problem."""
        return "Pressurized Pipe Network Optimization (Multi-objective)"


def evolve_ppno(optimization_instance: Any, 
                algorithm_factory: Any, 
                name: str,
                initial_x: Optional[np.ndarray] = None) -> Tuple[Optional[List[float]], Optional[np.ndarray]]:
    """Generic evolution loop for PyGMO algorithms.
    
    Evolves a population of solutions to find the best valid (max_deficit <= 0)
    solution with the minimum cost.
    """
    logger.info(f'*** {name} OPTIMIZATION ***')

    start_time = perf_counter()
    
    # Calculate how many simulation cycles occur per evaluation (number of time steps)
    # This is needed because PyGMO's internal copies of the instance don't update this one.
    initial_cycles = optimization_instance.simulation_cycles
    optimization_instance.check(mode='TF')
    # We determine how many cycles occur per evaluation (e.g., number of time steps)
    cycles_per_eval = max(1, optimization_instance.simulation_cycles - initial_cycles)
    # Note: pygmo copies the UDP, so we track evaluations through the pg.problem interface.

    prob = pg.problem(PPNOProblem(optimization_instance))

    total_generations = 0
    trials = 0
    consecutive_no_changes = 0

    best_cost_found: float = float('inf')
    best_valid_fitness: Optional[List[float]] = None
    best_valid_x: Optional[np.ndarray] = None

    # Initialize algorithm and population
    algorithm = pg.algorithm(algorithm_factory())
    population = pg.population(prob, size=POPULATION_SIZE)

    # Seed population with the initial solution and feasible variations
    if initial_x is not None:
        logger.info(f"      [SEEDED] Injecting initial solution into {name} population.")
        # Replace the first individual with the exact initial solution
        population.set_x(0, initial_x)
        
        # Replace other individuals with variations
        # We vary 5-10% of the variables for each individual to create diversity
        n_vars = len(initial_x)
        for i in range(1, min(10, POPULATION_SIZE)): # Seed first 10
            variant = initial_x.copy()
            n_change = max(1, int(n_vars * 0.05))
            idx_change = np.random.choice(n_vars, n_change, replace=False)
            for idx in idx_change:
                variant[idx] = np.clip(variant[idx] + np.random.randint(-1, 2), 
                                       optimization_instance.lbound[idx], 
                                       optimization_instance.ubound[idx])
            population.set_x(i, variant)

    while True:
        # Perform evolution step
        population = algorithm.evolve(population)
        trials += 1
        total_generations += GENERATIONS_PER_TRIAL

        # Search for the best valid solution in the current population
        fitness_values = population.get_f()
        solution_vectors = population.get_x()

        # Filter valid solutions and find the one with the minimum cost
        valid_solutions = [
            (fit, x) for fit, x in zip(fitness_values, solution_vectors)
            if fit[1] <= 0
        ]

        if valid_solutions:
            # Get valid solution with minimum cost
            current_best_fit, current_best_x = min(valid_solutions, key=lambda sol: sol[0][0])

            if current_best_fit[0] < best_cost_found:
                best_cost_found = current_best_fit[0]
                best_valid_fitness = list(current_best_fit)
                best_valid_x = current_best_x.copy()
                consecutive_no_changes = 0
            else:
                consecutive_no_changes += 1
        else:
            consecutive_no_changes += 1


        # Stopping criteria check
        elapsed_time = perf_counter() - start_time
        if elapsed_time >= MAX_ALGORITHM_TIME:
            logger.warning("Terminated: Maximum time reached.")
            break
        if trials >= MAX_TRIALS:
            logger.warning("Terminated: Maximum trials reached.")
            break
        if consecutive_no_changes >= MAX_NO_CHANGES:
            logger.info(f"Terminated: Converged after {consecutive_no_changes} trials without improvement.")
            break

    # Final sync of simulation cycles back to the main instance
    optimization_instance.simulation_cycles = population.problem.get_fevals() * cycles_per_eval

    return best_valid_fitness, best_valid_x


def nsga2(optimization_instance: Any, initial_x: Optional[np.ndarray] = None) -> Tuple[Optional[List[float]], Optional[np.ndarray]]:
    """Runs the Non-dominated Sorting Genetic Algorithm II."""
    return evolve_ppno(optimization_instance, lambda: pg.nsga2(gen=GENERATIONS_PER_TRIAL), "NSGA-II", initial_x)


def moead(optimization_instance: Any, initial_x: Optional[np.ndarray] = None) -> Tuple[Optional[List[float]], Optional[np.ndarray]]:
    """Runs Multi-Objective Evolutionary Algorithm based on Decomposition."""
    return evolve_ppno(optimization_instance, lambda: pg.moead(gen=GENERATIONS_PER_TRIAL), "MOEAD", initial_x)


def maco(optimization_instance: Any, initial_x: Optional[np.ndarray] = None) -> Tuple[Optional[List[float]], Optional[np.ndarray]]:
    """Runs Multi-objective Ant Colony Optimizer."""
    return evolve_ppno(optimization_instance, lambda: pg.maco(gen=GENERATIONS_PER_TRIAL), "MACO", initial_x)


def nspso(optimization_instance: Any, initial_x: Optional[np.ndarray] = None) -> Tuple[Optional[List[float]], Optional[np.ndarray]]:
    """Runs Non-dominated Sorting Particle Swarm Optimizer."""
    return evolve_ppno(optimization_instance, lambda: pg.nspso(gen=GENERATIONS_PER_TRIAL), "NSP-SO (PSO)", initial_x)

