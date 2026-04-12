"""Optimization module using Genetic Algorithms (NSGA-II) via PyGMO.

This module adapts the PPNO problem to the PyGMO framework for multi-objective
optimization, focusing on cost minimization and pressure constraint satisfaction.
"""

import logging
from time import perf_counter
from typing import Tuple, Optional, List, Any

import numpy as np
import pygmo as pg

# Logger configuration
logger = logging.getLogger(__name__)

# Default Evolution Parameters
GENERATIONS_PER_TRIAL = 100
POPULATION_SIZE = 100
MAX_TRIALS = 250
MAX_NO_CHANGES = 10
MAX_TIME_SECONDS = 10 * 60


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


def nsga2(optimization_instance: Any) -> Tuple[Optional[List[float]], Optional[np.ndarray]]:
    """Runs the Non-dominated Sorting Genetic Algorithm II (NSGA-II).

    Evolves a population of solutions to find the best valid (max_deficit <= 0)
    solution with the minimum cost.

    Args:
        optimization_instance: The optimization class instance to solve.

    Returns:
        A tuple (best_fitness, best_x) if a valid solution is found, else (None, None).
    """
    logger.info('*** NSGA-II EVOLUTIONARY OPTIMIZATION ***')

    start_time = perf_counter()
    prob = pg.problem(PPNOProblem(optimization_instance))
    
    total_generations = 0
    trials = 0
    consecutive_no_changes = 0
    
    best_cost_found: float = float('inf')
    best_valid_fitness: Optional[List[float]] = None
    best_valid_x: Optional[np.ndarray] = None

    # Configure NSGA-II algorithm
    algorithm = pg.algorithm(pg.nsga2(gen=GENERATIONS_PER_TRIAL))
    
    # Initialize random population
    population = pg.population(prob, size=POPULATION_SIZE)

    while True:
        # Perform evolution step
        population = algorithm.evolve(population)
        trials += 1
        total_generations += GENERATIONS_PER_TRIAL

        # Search for the best valid solution in the current population (Pareto Front)
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

        # Progress logging
        if best_valid_fitness:
            logger.info(f"Gen: {total_generations:5} | Best Cost: {best_valid_fitness[0]:12.2f} | Max Deficit: {best_valid_fitness[1]:6.3f}")

        # Stopping criteria check
        elapsed_time = perf_counter() - start_time
        if elapsed_time >= MAX_TIME_SECONDS:
            logger.warning("Terminated: Maximum time reached.")
            break
        if trials >= MAX_TRIALS:
            logger.warning("Terminated: Maximum trials reached.")
            break
        if consecutive_no_changes >= MAX_NO_CHANGES:
            logger.info(f"Terminated: Converged after {consecutive_no_changes} trials without improvement.")
            break

    return best_valid_fitness, best_valid_x
