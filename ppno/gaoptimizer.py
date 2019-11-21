# -*- coding: utf-8 -*-

"""PRESSURIZED PIPE NETWORK OPTIMIZER

https://github.com/andresgciamtez/ppno (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""

from time import perf_counter
import numpy as np
import pygmo as pg

# DECLARATIONS
GENERATIONS_PER_TRIAL = 100
POPULATION_SIZE = 100
MAX_TRIALS = 250
MAX_NO_CHANGES = 10
MAX_TIME = 10*60

class PPNOProblem():
    def __init__(self, ppn):
        self.mynet = ppn

    def fitness(self, x):
        tmp = np.array(x, dtype=np.int)
        self.mynet.set_x(tmp)
        f1 = float(self.mynet.get_cost())
        f2 = float(max(self.mynet.check(mode='PD')))
        return [f1, f2]

    def get_bounds(self):
        return self.mynet.lbound, self.mynet.ubound

    def get_nobj(self):
        return 2

    def get_nix(self):
        return self.mynet.dimension

    def get_name(self):
        return "Pressurized Pipe Network Optimization problem"

def nsga2(ppn):
    print('*** NSGA-II ALGORITHM ***')

    # INSTANCIATE A PYGMO PROBLEM CONSTRUCTING IT FROM A UDP
    inittime = perf_counter()
    prob = pg.problem(PPNOProblem(ppn))
    generations = trials = nochanges = 0
    best_f = best_x = None

    # INSTANCIATE THE PYGMO ALGORITM NSGA-II
    algo = pg.algorithm(pg.nsga2(gen=GENERATIONS_PER_TRIAL))

    # INSTANCIATE A POPULATION
    pop = pg.population(prob, size=POPULATION_SIZE)
    while True:

        # RUN THE EVOLUION
        pop = algo.evolve(pop)
        trials += 1
        generations += GENERATIONS_PER_TRIAL

        # EXTRACT RESULTS AND SEARCH THE BEST
        fits, vectors = pop.get_f(), pop.get_x()
        new_f = new_x = None
        for fit, vector in zip(fits, vectors):

            # VALID SOLUTION
            if fit[1] <= 0:
                if isinstance(new_f, type(None)):
                    new_f = fit
                    new_x = vector
                elif new_f[0] > fit[0]:
                    new_f = fit
                    new_x = vector
        if not isinstance(new_f, type(None)):
            if isinstance(best_f, type(None)):
                best_f = new_f
                best_x = new_x
            else:
                if best_f[0] > new_f[0]:
                    best_f = new_f
                    best_x = new_x
                    nochanges = 0
                else:
                    nochanges += 1
        if not isinstance(best_f, type(None)):
            print('Generations: %i '%(generations), end='')
            print('Cost: %.2f Pressure deficit: %0.3f '%(best_f[0], best_f[1]))
        if (perf_counter()-inittime) >= MAX_TIME:
            print('Maximum evolution time was reached.')
            break
        elif trials >= MAX_TRIALS:
            print('Maximum number of trials was reached.')
            break
        elif nochanges >= MAX_NO_CHANGES:
            print('Objective function value was repeated %i times.'%(nochanges))
            break
    return (best_f, best_x)
