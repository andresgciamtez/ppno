"""PRESSURIZED PIPE NETWORK OPTIMIZER.

A modern Python tool for optimizing pipe network diameters using various
algorithms (Unit Headloss Heuristic, Differential Evolution, Dual Annealing, NSGA-II).
"""

import sys
import logging
from time import perf_counter, localtime, strftime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any

import numpy as np
import toolkit as et
import section_parser as sp

# Logger configuration
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants
ALGORITHM_UH = 0
ALGORITHM_DE = 1
ALGORITHM_DA = 2
ALGORITHM_NSGA2 = 3
PENALTY_VALUE = 1e24


class Optimization:
    """Core class for pipe network optimization.

    Coordinates the hydraulic simulation and the optimization algorithms to
    find the best pipe diameters from a given catalog.

    Attributes:
        problem_file (Path): Path to the .ext problem definition file.
        inp_file (Path): Path to the original EPANET .inp file.
        rpt_file (Path): Path to the generated EPANET .rpt file.
        algorithm (int): Chosen optimization algorithm ID.
        refinement (bool): Whether to run a final refinement step.
        pipes (np.ndarray): Array of pipes to be sized.
        nodes (np.ndarray): Array of nodes to check for pressure requirements.
        catalog (Dict[str, np.ndarray]): Available pipe series and their properties.
        dimension (int): Number of variable pipes.
        lbound (np.ndarray): Lower bounds for variable indexes.
        ubound (np.ndarray): Upper bounds for variable indexes.
    """

    def __init__(self, problem_file: Union[str, Path]):
        """Initializes the optimization problem.

        Args:
            problem_file: Path to the .ext file containing problem data.

        Raises:
            FileNotFoundError: If the problem or input files are missing.
            ValueError: If mandatory sections are missing in the problem file.
        """
        self.problem_file = Path(problem_file)
        if not self.problem_file.exists():
            raise FileNotFoundError(f"Problem file not found: {self.problem_file}")

        parser = sp.SectionParser(self.problem_file)
        sections = parser.read()

        if 'INP' not in sections or not sections['INP']:
            raise ValueError("The [INP] section is missing or empty in the .ext file.")
        self.inp_file = Path(sections['INP'][0])
        self.rpt_file = self.inp_file.with_suffix('.rpt')

        logger.info(f"Loading optimization problem: {self.problem_file}")
        et.ENopen(str(self.inp_file), str(self.rpt_file))
        et.ENopenH()

        logger.info("-" * 80)
        logger.info(f"NETWORK DATA: {self.inp_file}")

        self._load_options(sections.get('OPTIONS', []), parser)
        self._load_pipes(sections.get('PIPES', []), parser)
        self._load_pressures(sections.get('PRESSURES', []), parser)
        self._load_catalog(sections.get('CATALOG', []), parser)

        self.dimension = len(self.pipes)
        self._current_x = np.zeros(self.dimension, dtype=np.int32)

        self.lbound = np.zeros(self.dimension, dtype=np.int32)
        self.ubound = np.array([len(self.catalog[str(p['series'])]) - 1 for p in self.pipes], dtype=np.int32)
        logger.info("-" * 80)

    def _load_options(self, options_lines: List[str], parser: sp.SectionParser) -> None:
        """Parses the OPTIONS section."""
        self.algorithm = ALGORITHM_UH
        self.refinement = False
        alg_map = {'UH': ALGORITHM_UH, 'DE': ALGORITHM_DE, 'DA': ALGORITHM_DA, 'NSGA2': ALGORITHM_NSGA2}

        msg = "Algorithm: "
        for line in options_lines:
            key, value = parser.line_to_tuple(line)
            if key.upper() == 'ALGORITHM':
                self.algorithm = alg_map.get(value.upper(), ALGORITHM_UH)
                msg += value
            elif key.upper() in ['POLISH', 'REFINEMENT', 'REFINE']:
                self.refinement = value.upper() in ['YES', 'Y']
                msg += " (with refinement)" if self.refinement else ""

        logger.info(msg)

    def _load_pipes(self, pipe_lines: List[str], parser: sp.SectionParser) -> None:
        """Parses the PIPES section."""
        dt = np.dtype([('link_idx', 'i4'), ('id', 'U16'), ('length', 'f4'), ('series', 'U16')])
        data = []
        for line in pipe_lines:
            pipe_id, series_name = parser.line_to_tuple(line)
            link_idx = et.ENgetlinkindex(pipe_id)
            length = et.ENgetlinkvalue(link_idx, et.EN_LENGTH)
            data.append((link_idx, pipe_id, length, series_name))

        self.pipes = np.array(data, dt)
        logger.info(f"Loaded {len(self.pipes)} pipes for sizing.")

    def _load_pressures(self, pressure_lines: List[str], parser: sp.SectionParser) -> None:
        """Parses the PRESSURES section."""
        dt = np.dtype([('node_idx', 'i4'), ('id', 'U16'), ('min_pressure', 'f4')])
        data = []
        for line in pressure_lines:
            node_id, min_p = parser.line_to_tuple(line)
            node_idx = et.ENgetnodeindex(node_id)
            data.append((node_idx, node_id, float(min_p)))

        self.nodes = np.array(data, dtype=dt)
        logger.info(f"Loaded {len(self.nodes)} pressure constraints.")

    def _load_catalog(self, catalog_lines: List[str], parser: sp.SectionParser) -> None:
        """Parses the CATALOG section."""
        dt = np.dtype([('diameter', 'f4'), ('roughness', 'f4'), ('price', 'f4')])
        required_series = set(str(p['series']) for p in self.pipes)

        raw_data: Dict[str, List[Tuple[float, float, float]]] = {s: [] for s in required_series}
        for line in catalog_lines:
            sn, d, r, p = parser.line_to_tuple(line)
            if sn in required_series:
                raw_data[sn].append((float(d), float(r), float(p)))

        self.catalog = {
            name: np.sort(np.array(data, dtype=dt), order='diameter')
            for name, data in raw_data.items()
        }
        logger.info(f"Loaded {len(self.catalog)} pipe series catalogs.")

    def set_x(self, x: np.ndarray) -> None:
        """Updates the hydraulic model with the new diameter indexes."""
        self._current_x = x.astype(np.int32)
        for i, pipe in enumerate(self.pipes):
            link_idx = int(pipe['link_idx'])
            series = self.catalog[str(pipe['series'])]
            size_idx = int(self._current_x[i])

            et.ENsetlinkvalue(link_idx, et.EN_DIAMETER, float(series[size_idx]['diameter']))
            et.ENsetlinkvalue(link_idx, et.EN_ROUGHNESS, float(series[size_idx]['roughness']))

    def get_x(self) -> np.ndarray:
        """Returns a copy of the current vector of diameter indexes."""
        return self._current_x.copy()

    def check(self, mode: str = 'TF') -> Union[bool, Tuple[bool, np.ndarray], np.ndarray]:
        """Checks pressure constraints across all time steps.

        Args:
            mode: 'TF' for boolean status, 'UH' for status and sorted headlosses,
                  'PD' for nodal pressure deficits.

        Returns:
            Depending on mode: bool, (bool, np.ndarray), or np.ndarray.
        """
        deficits = np.full(len(self.nodes), np.inf, dtype=np.float32) if mode == 'PD' else None
        max_hls = np.zeros(len(self.pipes), dtype=np.float32) if mode == 'UH' else None
        overall_status = True

        et.ENinitH(0)
        while True:
            et.ENrunH()

            # Check nodal pressures
            for i, node in enumerate(self.nodes):
                calculated_p = et.ENgetnodevalue(int(node['node_idx']), et.EN_PRESSURE)
                required_p = float(node['min_pressure'])
                deficit = required_p - calculated_p

                if deficit > 0:
                    overall_status = False

                if mode == 'PD' and deficits is not None:
                    if deficits[i] > deficit:
                        deficits[i] = deficit

            # Track link headlosses for UH mode
            if mode == 'UH' and max_hls is not None:
                for i in range(len(self.pipes)):
                    hl = et.ENgetlinkvalue(int(self.pipes[i]['link_idx']), et.EN_HEADLOSS)
                    if max_hls[i] < hl:
                        max_hls[i] = hl

            if et.ENnextH() == 0:
                break

        if mode == 'UH':
            sorted_indices = np.argsort(max_hls)[::-1]
            return overall_status, sorted_indices
        if mode == 'PD':
            return deficits if deficits is not None else np.array([])
        return overall_status

    def get_cost(self) -> float:
        """Calculates total network cost based on current sizing."""
        total = 0.0
        x = self.get_x()
        for i, pipe in enumerate(self.pipes):
            total += float(pipe['length']) * float(self.catalog[str(pipe['series'])][int(x[i])]['price'])
        return total

    def solve(self) -> Optional[np.ndarray]:
        """Executes the optimization process."""
        start_time = perf_counter()
        solution = None

        logger.info(f"Optimization started at: {strftime('%H:%M:%S', localtime())}")

        if self.algorithm == ALGORITHM_UH:
            solution = self._solve_uh()
        elif self.algorithm in [ALGORITHM_DE, ALGORITHM_DA]:
            solution = self._solve_scipy()
        elif self.algorithm == ALGORITHM_NSGA2:
            from gao import nsga2
            _, sol_x = nsga2(self)
            solution = np.array(sol_x, dtype=np.int32) if sol_x is not None else None

        if self.refinement and solution is not None:
            solution = self._apply_refinement(solution)

        if solution is not None:
            self._handle_success(solution)
        else:
            logger.error("No valid solution found.")

        logger.info(f"Duration: {perf_counter() - start_time:.2f}s")
        return solution

    def _solve_uh(self) -> Optional[np.ndarray]:
        """Unit Headloss Heuristic logic."""
        logger.info("*** UNIT HEADLOSS HEURISTIC ***")
        self.set_x(np.zeros(self.dimension, dtype=np.int32))
        while True:
            status, sorted_hls = self.check(mode='UH')
            if status:
                return self.get_x().copy()

            expanded = False
            for idx in sorted_hls:
                x = self.get_x().copy()
                if x[idx] < self.ubound[idx]:
                    x[idx] += 1
                    self.set_x(x)
                    expanded = True
                    break
            if not expanded:
                return None

    def _solve_scipy(self) -> Optional[np.ndarray]:
        """SciPy optimization wrapper."""
        bounds = list(zip(self.lbound, self.ubound))

        def objective(x_params):
            self.set_x(np.round(x_params).astype(np.int32))
            return self.get_cost() if self.check(mode='TF') else PENALTY_VALUE

        if self.algorithm == ALGORITHM_DE:
            from scipy.optimize import differential_evolution
            logger.info("*** DIFFERENTIAL EVOLUTION ***")
            result = differential_evolution(objective, bounds)
        else:
            from scipy.optimize import dual_annealing
            logger.info("*** DUAL ANNEALING ***")
            result = dual_annealing(objective, bounds)

        final_x = np.round(result.x).astype(np.int32)
        self.set_x(final_x)
        return final_x if self.check(mode='TF') else None

    def _apply_refinement(self, solution: np.ndarray) -> np.ndarray:
        """Manual refinement to reduce diameters of non-critical pipes."""
        logger.info("+++ APPLYING REFINEMENT +++")
        refined = solution.copy()
        # Simplified greedy approach: try to reduce each pipe price-wise
        indices_by_saving = sorted(range(self.dimension), 
                                   key=lambda i: float(self.catalog[str(self.pipes[i]['series'])][int(solution[i])]['price']),
                                   reverse=True)

        for idx in indices_by_saving:
            while refined[idx] > 0:
                refined[idx] -= 1
                self.set_x(refined)
                if not self.check(mode='TF'):
                    refined[idx] += 1 # Undo
                    break
                logger.debug(f"Reduced pipe {self.pipes[idx]['id']}")

        return refined

    def _handle_success(self, solution: np.ndarray) -> None:
        """Saves and prints results for a successful run."""
        self.set_x(solution)
        cost = self.get_cost()
        logger.info(f"Success! Final Network Cost: {cost:.2f}")

        alg_name = {ALGORITHM_UH: 'UH', ALGORITHM_DE: 'DE', ALGORITHM_DA: 'DA', ALGORITHM_NSGA2: 'NSGA2'}[self.algorithm]
        out_path = self.inp_file.parent / (self.inp_file.stem + f"_Solved_{alg_name}.inp")
        et.ENsaveinpfile(str(out_path))
        logger.info(f"Optimized model saved to: {out_path}")

    def pretty_print(self, x: np.ndarray) -> None:
        """Displays the solution in a formatted table."""
        logger.info("\n" + "*" * 20 + " FINAL SOLUTION " + "*" * 20)
        logger.info(f"{'Pipe ID':>16} {'Series':>12} {'Diam':>8} {'Rough':>8} {'Len':>8} {'Price':>8} {'Total':>10}")
        logger.info("-" * 80)

        for i, pipe in enumerate(self.pipes):
            size = int(x[i])
            cat = self.catalog[str(pipe['series'])][size]
            d, r, p = float(cat['diameter']), float(cat['roughness']), float(cat['price'])
            length = float(pipe['length'])
            logger.info(f"{str(pipe['id']):>16} {str(pipe['series']):>12} {d:8.1f} {r:8.4f} {length:8.1f} {p:8.2f} {length * p:10.2f}")

        logger.info("-" * 80)
        logger.info(f"TOTAL NETWORK COST: {self.get_cost():.2f}")
        logger.info("*" * 56 + "\n")

    def close(self) -> None:
        """Safely closes the EPANET toolkit."""
        try:
            et.ENcloseH()
            et.ENclose()
        except Exception:
            pass


def main(argv: Optional[List[str]] = None) -> None:
    """Entry point for the PPNO command-line tool."""
    if argv is None:
        argv = sys.argv
    if len(argv) < 2:
        logger.error("Usage: ppno <problem_file.ext>")
        return

    logger.info("=" * 80)
    logger.info(" PRESSURIZED PIPE NETWORK OPTIMIZER ")
    logger.info("=" * 80)

    opt = None
    try:
        opt = Optimization(argv[1])
        solution = opt.solve()
        if solution is not None:
            opt.pretty_print(solution)
    except Exception:
        logger.exception("A fatal error occurred during optimization:")
    finally:
        if opt is not None:
            opt.close()


if __name__ == "__main__":
    main(sys.argv)
