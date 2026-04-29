"""Optimization module using SciPy algorithms.

This module provides wrappers for various SciPy global optimization algorithms
adapted for the pipe network optimization problem.
"""

import logging
from typing import Optional
from time import perf_counter
import numpy as np
from .constants import (
    ALGORITHM_DE, ALGORITHM_DA, ALGORITHM_DIRECT, 
    PENALTY_VALUE, MAX_ALGORITHM_TIME
)

# Logger configuration
logger = logging.getLogger(__name__)


class SolverTimeoutError(Exception):
    """Exception raised when an optimization solver exceeds its time limit."""
    pass


def solve_scipy(opt_instance, alg_id: int, initial_x: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
    """Wrap SciPy global optimization algorithms for pipe network optimization.

    This function configures and executes SciPy's continuous global optimizers
    (Differential Evolution, Dual Annealing, or DIRECT). Since these optimizers
    work with continuous variables, the objective function automatically rounds
    candidate vectors to the nearest integer index to map them to discrete catalog entries.

    The objective function employs a guided penalty mechanism:
    - If the solution is feasible, the true network cost is returned.
    - If infeasible, a large constant penalty is added, plus an amount proportional
      to the maximum pressure deficit. This gradient guides the optimizer towards 
      feasible regions.

    Args:
        opt_instance (Any): An instance of the Optimization class providing bounds and evaluation methods.
        alg_id (int): The specific SciPy algorithm identifier (ALGORITHM_DE, ALGORITHM_DA, ALGORITHM_DIRECT).
        initial_x (Optional[np.ndarray]): An optional pre-computed feasible solution vector (e.g., from FLS-H)
                   used to seed the initial population or starting point.

    Returns:
        Optional[np.ndarray]: The optimized discrete diameter index vector, or None 
                               if the optimizer fails or times out.
    """
    bounds = list(zip(opt_instance.lbound, opt_instance.ubound))
    start_time = perf_counter()

    def objective(x_params):
        max_time = opt_instance.config.get('MaxTime', 120)
        if perf_counter() - start_time > max_time:
            raise SolverTimeoutError(f"Time limit of {max_time}s reached.")
        opt_instance.set_x(np.round(x_params).astype(np.int32))
        
        # We use mode 'PD' to get the maximum deficit for a guided penalty
        deficits = opt_instance.check(mode='PD')
        max_deficit = np.max(deficits)
        
        if max_deficit <= 0:
            return opt_instance.get_cost()
        else:
            # Provide a guided penalty proportional to the violation
            return PENALTY_VALUE + (max_deficit * 1e6)


    try:
        if alg_id == ALGORITHM_DE:
            from scipy.optimize import differential_evolution
            logger.info("*** DIFFERENTIAL EVOLUTION ***")
            
            popsize_factor = 15
            n_vars = len(opt_instance.lbound)
            m_total = popsize_factor * n_vars
            
            init_pop = np.zeros((m_total, n_vars))
            for j in range(n_vars):
                low, high = opt_instance.lbound[j], opt_instance.ubound[j]
                init_pop[:, j] = np.random.uniform(low, high, m_total)
            
            if initial_x is not None:
                logger.info("      [SEEDED] Injecting initial solution into DE population.")
                init_pop[0] = initial_x.astype(np.float64)
            
            result = differential_evolution(objective, bounds, init=init_pop, 
                                            popsize=popsize_factor)
        elif alg_id == ALGORITHM_DA:
            from scipy.optimize import dual_annealing
            logger.info("*** DUAL ANNEALING ***")
            if initial_x is not None:
                logger.info("      [SEEDED] Using initial solution as starting point for DA.")
            result = dual_annealing(objective, bounds, x0=initial_x)
        elif alg_id == ALGORITHM_DIRECT:
            from scipy.optimize import direct
            logger.info("*** DIRECT ***")
            # DIRECT does not accept an initial point (x0). It deterministically
            # subdivides the search space from the center of the hypercube.
            result = direct(objective, bounds)
        else:
            return None

        if not result.success:
            return None

        final_x = np.round(result.x).astype(np.int32)
        opt_instance.set_x(final_x)
        return final_x if opt_instance.check(mode='TF') else None

    except SolverTimeoutError as e:
        logger.warning(str(e))
        return None
