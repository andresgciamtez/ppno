"""PRESSURIZED PIPE NETWORK OPTIMIZER.

A modern Python tool for optimizing pipe network diameters using various
algorithms (Unit Headloss Heuristic, Differential Evolution, Dual Annealing, NSGA-II).
"""

import os
import sys
import logging
from time import perf_counter, localtime, strftime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any

import numpy as np
from entoolkit import toolkit as et
from . import section_parser as sp
from .local_refiner import LocalRefiner

# Logger configuration
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants
from .constants import (
    ALGORITHM_UH, ALGORITHM_DE, ALGORITHM_DA, ALGORITHM_NSGA2,
    ALGORITHM_DIRECT, ALGORITHM_MOEAD, ALGORITHM_MACO,
    ALGORITHM_PSO, MAX_RETRIES,
    LS_MAX_ITER, LS_ACCEPTANCE_THRESHOLD, LS_NEIGHBORHOOD_SIZE
)


class Optimization:
    """Core class for pipe network optimization.

    Coordinates the hydraulic simulation and the optimization algorithms to
    find the best pipe diameters from a given catalog.

    Attributes:
        problem_file (Path): Path to the .ext problem definition file.
        inp_file (Path): Path to the original EPANET .inp file.
        rpt_file (Path): Path to the generated EPANET .rpt file.
        algorithm (int): Chosen optimization algorithm ID.
        pipes (np.ndarray): Array of pipes to be sized.
        nodes (np.ndarray): Array of nodes to check for pressure requirements.
        catalog (Dict[str, np.ndarray]): Available pipe series and their properties.
        dimension (int): Number of variable pipes.
        lbound (np.ndarray): Lower bounds for variable indexes.
        ubound (np.ndarray): Upper bounds for variable indexes.
        algorithms (List[int]): List of Stage 2 metaheuristic algorithms to execute.
        max_retries (int): Maximum retry attempts for failed algorithms.
        simulation_cycles (int): Counter for network hydraulic simulation runs.
        results (List[Dict[str, Any]]): Collected performance data.
    """

    def __init__(self, problem_file: Union[str, Path]):
        """Initializes the optimization problem and performs full validation.

        Args:
            problem_file: Path to the .ext file containing problem data.

        Raises:
            FileNotFoundError: If the problem or input files are missing.
            ValueError: If configuration validation fails (syntax, existence, or logic).
        """
        self.problem_file = Path(problem_file)
        if not self.problem_file.exists():
            raise FileNotFoundError(f"Problem file not found: {self.problem_file}")

        parser = sp.SectionParser(self.problem_file)
        sections = parser.read()

        # 1. Verify INP Section
        if 'INP' not in sections or not sections['INP']:
            raise ValueError(f"Line 1: Mandatory [INP] section is missing or empty in {self.problem_file.name}")
        
        inp_line_num, inp_raw_path = sections['INP'][0]
        inp_path = Path(inp_raw_path)
        if not inp_path.exists():
            # If not found at the specified path, try relative to the .ext file (only filename)
            inp_path = self.problem_file.parent / inp_path.name
            
        if not inp_path.exists():
             raise FileNotFoundError(f"Line {inp_line_num}: EPANET INP file not found: {inp_raw_path}")

        self.inp_file = inp_path
        self.rpt_file = self.inp_file.with_suffix('.rpt')
        self.report_enabled = False
        self.algorithm = ALGORITHM_UH

        # 2. Open Toolkit for entity validation
        rpt = os.devnull
        try:
            et.ENopen(str(self.inp_file), rpt)
        except Exception as e:
            raise ValueError(f"Line {inp_line_num}: Failed to load EPANET model {self.inp_file.name} ({str(e)})")
        
        et.ENopenH()
        try:
            et.ENsetstatusreport(0)
        except Exception:
            pass

        # 3. Comprehensive Validation
        self._validate_config(sections, parser)

        # 4. Load Data
        self._load_options(sections.get('OPTIONS', []), parser)

        logger.info(f"Loading optimization problem: {self.problem_file}")
        logger.info("-" * 80)
        logger.info(f"NETWORK DATA: {self.inp_file}")

        self._load_pipes(sections.get('PIPES', []), parser)
        self._load_pressures(sections.get('PRESSURES', []), parser)
        self._load_catalog(sections.get('CATALOG', []), parser)

        self.dimension = len(self.pipes)
        self._current_x = np.zeros(self.dimension, dtype=np.int32)
        self.lbound = np.zeros(self.dimension, dtype=np.int32)
        self.ubound = np.array([len(self.catalog[str(p['series'])]) - 1 for p in self.pipes], dtype=np.int32)
        
        self.simulation_cycles = 0
        self.results = []
        logger.info("-" * 80)

    def _validate_config(self, sections: Dict[str, List[Tuple[int, str]]], parser: sp.SectionParser) -> None:
        """Performs semantic validation of the configuration."""
        errors = []
        
        # Check Algorithms
        alg_map = {'UH', 'DE', 'DA', 'NSGA2', 'DIRECT', 'MOEAD', 'MACO', 'PSO'}
        options = sections.get('OPTIONS', [])
        for line_num, content in options:
            tokens = parser.line_to_tuple(content)
            if not tokens: continue
            tokens = [t for t in tokens if t != '=']
            key = tokens[0].upper().replace('_', '')
            if key in ['ALGORITHM', 'ALGORITHMS']:
                for val in tokens[1:]:
                    if val.upper() not in alg_map:
                        errors.append(f"Line {line_num}: Unknown algorithm '{val}'")

        # Check Pipes Existence and Series
        pipes_lines = sections.get('PIPES', [])
        catalog_names = set()
        for _, content in sections.get('CATALOG', []):
            tokens = parser.line_to_tuple(content)
            if tokens: catalog_names.add(tokens[0])

        for line_num, content in pipes_lines:
            tokens = parser.line_to_tuple(content)
            if len(tokens) < 2:
                errors.append(f"Line {line_num}: Invalid pipe definition. Expected 'ID SERIES'")
                continue
            pipe_id, series_name = tokens[0], tokens[1]
            try:
                et.ENgetlinkindex(pipe_id)
            except Exception:
                errors.append(f"Line {line_num}: Pipe '{pipe_id}' not found in hydraulic model")
            
            if series_name not in catalog_names:
                errors.append(f"Line {line_num}: Catalog series '{series_name}' not defined in [CATALOG]")

        # Check Nodes and Pressures
        pressures_lines = sections.get('PRESSURES', [])
        for line_num, content in pressures_lines:
            tokens = parser.line_to_tuple(content)
            if len(tokens) < 2:
                errors.append(f"Line {line_num}: Invalid pressure definition. Expected 'ID MIN_PRESSURE'")
                continue
            node_id, min_p = tokens[0], tokens[1]
            try:
                et.ENgetnodeindex(node_id)
            except Exception:
                errors.append(f"Line {line_num}: Node '{node_id}' not found in hydraulic model")
            try:
                float(min_p)
            except ValueError:
                errors.append(f"Line {line_num}: Invalid pressure value '{min_p}'")

        # Check Catalog Consistency (Strictly Increasing Diameter)
        temp_cat = {}
        for line_num, content in sections.get('CATALOG', []):
            tokens = parser.line_to_tuple(content)
            if len(tokens) < 4: continue
            sn, d, r, p = tokens[0], float(tokens[1]), float(tokens[2]), float(tokens[3])
            if sn not in temp_cat: temp_cat[sn] = []
            temp_cat[sn].append({'d': d, 'p': p, 'line': line_num})

        for sn, items in temp_cat.items():
            for i in range(1, len(items)):
                if items[i]['d'] <= items[i-1]['d']:
                    errors.append(f"Line {items[i]['line']}: Diameter must be strictly increasing in series '{sn}'")
                if items[i]['p'] <= items[i-1]['p']:
                     logger.warning(f"Line {items[i]['line']}: Price {items[i]['p']} is not greater than {items[i-1]['p']} for larger diameter (Anomalous)")

        if errors:
            raise ValueError("Configuration Validation Failed:\n" + "\n".join(errors))

    def _load_options(self, options_lines: List[Tuple[int, str]], parser: sp.SectionParser) -> None:
        """Parses the OPTIONS section."""
        self.algorithms = []  # Stage 2 metaheuristics; empty = only UH + FLS-H
        self.max_retries = MAX_RETRIES
        alg_map = {
            'UH': ALGORITHM_UH, 
            'DE': ALGORITHM_DE, 
            'DA': ALGORITHM_DA, 
            'NSGA2': ALGORITHM_NSGA2, 
            'DIRECT': ALGORITHM_DIRECT,
            'MOEAD': ALGORITHM_MOEAD,
            'MACO': ALGORITHM_MACO,
            'PSO': ALGORITHM_PSO
        }

        for line_num, content in options_lines:
            tokens = parser.line_to_tuple(content)
            if not tokens:
                continue
            
            # Filter out '=' if present
            tokens = [t for t in tokens if t != '=']
            if not tokens:
                continue

            key = tokens[0].upper().replace('_', '') # Normalize: remove underscores
            values = tokens[1:]

            if key in ['ALGORITHM', 'ALGORITHMS'] and values:
                self.algorithms = [alg_map.get(v.upper(), None) for v in values]
                self.algorithms = [a for a in self.algorithms if a is not None and a != ALGORITHM_UH]
                logger.info(f"Optional Metaheuristics: {', '.join(values)}")
            elif key in ['MAXRETRIES', 'RETRIES']:
                if values:
                    self.max_retries = int(values[0])
                    logger.info(f"Max Retries: {self.max_retries}")
            elif key in ['REPORT', 'GENERATERPT', 'REPORTFILE']:
                if values:
                    self.report_enabled = values[0].upper() in ['YES', 'Y', 'TRUE']
                    logger.info(f"Generate RPT File: {self.report_enabled}")

    def _load_pipes(self, pipe_lines: List[Tuple[int, str]], parser: sp.SectionParser) -> None:
        """Parses the PIPES section."""
        dt = np.dtype([('link_idx', 'i4'), ('id', 'U16'), ('length', 'f4'), ('series', 'U16')])
        data = []
        for line_num, content in pipe_lines:
            tokens = parser.line_to_tuple(content)
            pipe_id, series_name = tokens[0], tokens[1]
            link_idx = et.ENgetlinkindex(pipe_id)
            length = et.ENgetlinkvalue(link_idx, et.EN_LENGTH)
            data.append((link_idx, pipe_id, length, series_name))

        self.pipes = np.array(data, dt)
        logger.info(f"Loaded {len(self.pipes)} pipes for sizing.")

    def _load_pressures(self, pressure_lines: List[Tuple[int, str]], parser: sp.SectionParser) -> None:
        """Parses the PRESSURES section."""
        dt = np.dtype([('node_idx', 'i4'), ('id', 'U16'), ('min_pressure', 'f4')])
        data = []
        for line_num, content in pressure_lines:
            tokens = parser.line_to_tuple(content)
            node_id, min_p = tokens[0], tokens[1]
            node_idx = et.ENgetnodeindex(node_id)
            data.append((node_idx, node_id, float(min_p)))

        self.nodes = np.array(data, dtype=dt)
        logger.info(f"Loaded {len(self.nodes)} pressure constraints.")

    def _load_catalog(self, catalog_lines: List[Tuple[int, str]], parser: sp.SectionParser) -> None:
        """Parses the CATALOG section."""
        dt = np.dtype([('diameter', 'f4'), ('roughness', 'f4'), ('price', 'f4')])
        required_series = set(str(p['series']) for p in self.pipes)

        raw_data: Dict[str, List[Tuple[float, float, float]]] = {s: [] for s in required_series}
        for line_num, content in catalog_lines:
            tokens = parser.line_to_tuple(content)
            sn, d, r, p = tokens[0], tokens[1], tokens[2], tokens[3]
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

            try:
                et.ENsetlinkvalue(link_idx, et.EN_DIAMETER, float(series[size_idx]['diameter']))
                et.ENsetlinkvalue(link_idx, et.EN_ROUGHNESS, float(series[size_idx]['roughness']))
            except Exception:
                pass

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
        deficits = np.full(len(self.nodes), -1e10, dtype=np.float32) if mode == 'PD' else None
        max_hls = np.zeros(len(self.pipes), dtype=np.float32) if mode == 'UH' else None
        overall_status = True

        try:
            et.ENinitH(0)
            while True:
                et.ENrunH()
                self.simulation_cycles += 1

                # Check nodal pressures
                for i, node in enumerate(self.nodes):
                    calculated_p = et.ENgetnodevalue(int(node['node_idx']), et.EN_PRESSURE)
                    required_p = float(node['min_pressure'])
                    deficit = required_p - calculated_p

                    if deficit > 0:
                        overall_status = False

                    if mode == 'PD' and deficits is not None:
                        if deficits[i] < deficit:
                            deficits[i] = deficit

                # Track link headlosses for UH mode
                if mode == 'UH' and max_hls is not None:
                    for i in range(len(self.pipes)):
                        hl = et.ENgetlinkvalue(int(self.pipes[i]['link_idx']), et.EN_HEADLOSS)
                        gradient = abs(hl) / float(self.pipes[i]['length'])
                        if max_hls[i] < gradient:
                            max_hls[i] = gradient

                if et.ENnextH() == 0:
                    break
        except Exception:
            pass

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
        """Executes the two-stage optimization pipeline: UH+FLS-H foundation,
        followed by optional metaheuristic exploration also finished with FLS-H."""
        self.results = []
        self.simulation_cycles = 0
        logger.info(f"Optimization pipeline started at: {strftime('%H:%M:%S', localtime())}")

        # --- STAGE 1: Mandatory Foundation (UH + LS) ---
        logger.info("\n" + ">>> STAGE 1: HEURISTIC FOUNDATION (UH + FLS-H) <<<")
        start_time_s1 = perf_counter()
        
        # 1a. UH Heuristic
        solution = self._solve_uh()
        if solution is None:
            logger.error("Stage 1 failed: Unit Headloss Heuristic could not find a solution.")
            return None
        
        # 1b. Refinement (FLS-H) - always applied
        solution = self._apply_refinement(solution)
        
        duration_s1 = perf_counter() - start_time_s1
        self.set_x(solution)
        cost_s1 = self.get_cost()
        
        logger.info(f"Stage 1 Complete | Cost: {cost_s1:.2f} | Time: {duration_s1:.2f}s")
        
        self.results.append({
            'Algorithm': 'Foundation',
            'Attempt': 1,
            'Success': "YES",
            'Time (s)': f"{duration_s1:.2f}",
            'Simulations': self.simulation_cycles,
            'Cost': f"{cost_s1:.2f}"
        })
        
        overall_best_solution = solution.copy()
        overall_best_cost = cost_s1

        # --- STAGE 2: Optional Global Exploration (Metaheuristics) ---
        if self.algorithms:
            logger.info("\n" + ">>> STAGE 2: OPTIONAL GLOBAL EXPLORATION <<<")
            
            alg_names = {
                ALGORITHM_DE: 'DE', ALGORITHM_DA: 'DA', ALGORITHM_NSGA2: 'NSGA2',
                ALGORITHM_DIRECT: 'DIRECT', ALGORITHM_MOEAD: 'MOEAD',
                ALGORITHM_MACO: 'MACO', ALGORITHM_PSO: 'PSO'
            }

            for alg_id in self.algorithms:
                alg_name = alg_names.get(alg_id, 'UNKNOWN')
                
                for attempt in range(1, self.max_retries + 1):
                    logger.info("-" * 40)
                    logger.info(f"ALGORITHM: {alg_name} (Attempt {attempt}/{self.max_retries})")
                    
                    start_time = perf_counter()
                    self.simulation_cycles = 0
                    self.algorithm = alg_id
                    
                    # Run metaheuristic seeded with the current best solution
                    logger.info(f"      [SEED] Starting with best cost: {overall_best_cost:.2f}")
                    meta_solution = None
                    if alg_id in [ALGORITHM_DE, ALGORITHM_DA, ALGORITHM_DIRECT]:
                        from . import scipy_solver
                        meta_solution = scipy_solver.solve_scipy(self, alg_id, initial_x=overall_best_solution)
                    elif alg_id in [ALGORITHM_NSGA2, ALGORITHM_MOEAD, ALGORITHM_MACO, ALGORITHM_PSO]:
                        from . import pygmo_solver
                        sol_f, sol_x = (None, None)
                        if alg_id == ALGORITHM_NSGA2:
                            sol_f, sol_x = pygmo_solver.nsga2(self, initial_x=overall_best_solution)
                        elif alg_id == ALGORITHM_MOEAD:
                            sol_f, sol_x = pygmo_solver.moead(self, initial_x=overall_best_solution)
                        elif alg_id == ALGORITHM_MACO:
                            sol_f, sol_x = pygmo_solver.maco(self, initial_x=overall_best_solution)
                        elif alg_id == ALGORITHM_PSO:
                            sol_f, sol_x = pygmo_solver.nspso(self, initial_x=overall_best_solution)
                        
                        meta_solution = np.array(sol_x, dtype=np.int32) if sol_x is not None else None

                    duration = perf_counter() - start_time
                    success = meta_solution is not None
                    
                    if success:
                        self.set_x(meta_solution)
                        meta_cost = self.get_cost()
                        
                        if meta_cost < overall_best_cost:
                            logger.info(f"      [ACCEPTED] Improved cost found: {meta_cost:.2f} (Previous: {overall_best_cost:.2f})")
                            overall_best_cost = meta_cost
                            overall_best_solution = meta_solution.copy()
                        else:
                            logger.info(f"      [DISCARDED] Cost {meta_cost:.2f} is not an improvement over {overall_best_cost:.2f}")
                        
                        self.results.append({
                            'Algorithm': alg_name, 'Attempt': attempt, 'Success': "YES",
                            'Time (s)': f"{duration:.2f}", 'Simulations': self.simulation_cycles,
                            'Cost': f"{meta_cost:.2f}"
                        })
                        break
                    else:
                        self.results.append({
                            'Algorithm': alg_name, 'Attempt': attempt, 'Success': "NO",
                            'Time (s)': f"{duration:.2f}", 'Simulations': self.simulation_cycles, 'Cost': "-"
                        })

            # Apply refinement to the best solution found in Stage 2
            logger.info("\n>>> REFINING BEST SOLUTION (FLS-H) <<<")
            start_time_ref = perf_counter()
            overall_best_solution = self._apply_refinement(overall_best_solution)
            duration_ref = perf_counter() - start_time_ref
            self.set_x(overall_best_solution)
            refined_cost = self.get_cost()
            logger.info(f"Refinement Complete | Cost: {refined_cost:.2f} | Time: {duration_ref:.2f}s")
        else:
            logger.info("\n>>> STAGE 2 Skipped: No global exploration requested <<<")

        self._print_summary()
        self.set_x(overall_best_solution)
        self._handle_success(overall_best_solution)
        
        return overall_best_solution

    def _print_summary(self) -> None:
        """Displays a summary of all optimization runs (aggregated by algorithm)."""
        logger.info("\n" + "=" * 80)
        logger.info(f"{'ALGORITHM SUMMARY':^80}")
        logger.info("=" * 80)
        header = f"{'Algorithm':<14} {'Tries':<7} {'Success':<8} {'Time(s)':>10} {'Sims':>10} {'Best Cost':>15}"
        logger.info(header)
        logger.info("-" * 80)
        
        aggregated = {}
        for res in self.results:
            name = res['Algorithm']
            if name not in aggregated:
                aggregated[name] = {
                    'tries': 0,
                    'success': "NO",
                    'time': 0.0,
                    'sims': 0,
                    'cost': float('inf')
                }
            
            stats = aggregated[name]
            stats['tries'] += 1
            if res['Success'] == "YES":
                stats['success'] = "YES"
            
            stats['time'] += float(res['Time (s)'])
            stats['sims'] += int(res['Simulations'])
            
            if res['Cost'] != "-":
                stats['cost'] = min(stats['cost'], float(res['Cost']))

        for name, stats in aggregated.items():
            cost_str = f"{stats['cost']:.2f}" if stats['cost'] != float('inf') else "-"
            row = (f"{name:<14} {stats['tries']:<7} {stats['success']:<8} "
                   f"{stats['time']:>10.2f} {stats['sims']:>10} {cost_str:>15}")
            logger.info(row)
        logger.info("=" * 80 + "\n")

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


    def _apply_refinement(self, solution: np.ndarray) -> np.ndarray:
        """Applies FLS-H refined local search to the current solution."""
        config = {
            'max_iter': LS_MAX_ITER,
            'acceptance_threshold': LS_ACCEPTANCE_THRESHOLD,
            'neighborhood_size': LS_NEIGHBORHOOD_SIZE
        }
        
        refiner = LocalRefiner(self, config)
        refined_solution = refiner.refine(solution)
        
        return refined_solution

    def _handle_success(self, solution: np.ndarray) -> None:
        """Saves and prints results for a successful run."""
        self.set_x(solution)
        cost = self.get_cost()
        logger.info(f"Success! Final Network Cost: {cost:.2f}")

        alg_name = {
            ALGORITHM_UH: 'UH', 
            ALGORITHM_DE: 'DE', 
            ALGORITHM_DA: 'DA', 
            ALGORITHM_NSGA2: 'NSGA2',
            ALGORITHM_DIRECT: 'DIRECT',
            ALGORITHM_MOEAD: 'MOEAD',
            ALGORITHM_MACO: 'MACO',
            ALGORITHM_PSO: 'PSO'
        }.get(self.algorithm, 'Optimized')
        if self.report_enabled:
            try:
                et.ENsaveH()
                et.ENreport()
            except Exception:
                pass

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
    if len(argv) < 2 or argv[1] in ['-h', '--help']:
        print("Usage: ppno <problem_file.ext>")
        sys.exit(0)

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
        sys.exit(1)
    finally:
        if opt is not None:
            opt.close()


if __name__ == "__main__":
    main(sys.argv)
