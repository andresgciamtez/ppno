"""Optimization module using SciPy algorithms.

This module provides wrappers for various SciPy global optimization algorithms
adapted for the pipe network optimization problem.
"""

import logging
from typing import Optional
from time import perf_counter
import numpy as np
from .constants import (
    ALGORITHM_DE, ALGORITHM_DA, ALGORITHM_SHGO, ALGORITHM_DIRECT, 
    PENALTY_VALUE, MAX_ALGORITHM_TIME
)

# Configuration


# Logger configuration
logger = logging.getLogger(__name__)


class SolverTimeoutError(Exception):
    """Exception raised when an optimization solver exceeds its time limit."""
    pass


def solve_scipy(opt_instance, alg_id: int) -> Optional[np.ndarray]:
    """Wraps SciPy global optimization algorithms.

    Args:
        opt_instance: An instance of the Optimization class.
        alg_id: The specific SciPy algorithm to use.

    Returns:
        The optimized diameter index vector or None if failed.
    """
    bounds = list(zip(opt_instance.lbound, opt_instance.ubound))
    start_time = perf_counter()

    def objective(x_params):
        if perf_counter() - start_time > MAX_ALGORITHM_TIME:
            raise SolverTimeoutError(f"Time limit of {MAX_ALGORITHM_TIME}s reached.")
        
        opt_instance.set_x(np.round(x_params).astype(np.int32))
        return opt_instance.get_cost() if opt_instance.check(mode='TF') else PENALTY_VALUE

    try:
        if alg_id == ALGORITHM_DE:
            from scipy.optimize import differential_evolution
            logger.info("*** DIFFERENTIAL EVOLUTION ***")
            result = differential_evolution(objective, bounds)
        elif alg_id == ALGORITHM_DA:
            from scipy.optimize import dual_annealing
            logger.info("*** DUAL ANNEALING ***")
            result = dual_annealing(objective, bounds)
        elif alg_id == ALGORITHM_SHGO:
            from scipy.optimize import shgo
            logger.info("*** SHGO ***")
            result = shgo(objective, bounds)
        elif alg_id == ALGORITHM_DIRECT:
            from scipy.optimize import direct
            logger.info("*** DIRECT ***")
            result = direct(objective, bounds)
        else:
            return None

        final_x = np.round(result.x).astype(np.int32)
        opt_instance.set_x(final_x)
        return final_x if opt_instance.check(mode='TF') else None

    except SolverTimeoutError as e:
        logger.warning(str(e))
        return None
