# -*- coding: utf-8 -*-
"""PRESSURIZED PIPE NETWORK OPTIMIZING BY PYGMO
Andrés García Martínez (agarciam@citop.es)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""

from time import perf_counter
import numpy as np
import pygmo as pg

# PARAMETERS
GENERATIONSPERTRIAL = 100
POPULATIONSIZE = 100
MAXTRIALS = 250
MAXNOCHANGES = 10
MAXTIME = 10*60

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
        lb = self.mynet.lbound
        ub = self.mynet.ubound
        return (lb, ub)

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
    algo = pg.algorithm(pg.nsga2(gen=GENERATIONSPERTRIAL))
    # INSTANCIATE A POPULATION
    pop = pg.population(prob, size=POPULATIONSIZE)
    while True:
        # RUN THE EVOLUION
        pop = algo.evolve(pop)
        trials += 1
        generations += GENERATIONSPERTRIAL
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

        if (perf_counter()-inittime) >= MAXTIME:
            print('Maximum evolution time was reached.')
            break
        elif trials >= MAXTRIALS:
            print('Maximum number of trials was reached.')
            break
        elif nochanges >= MAXNOCHANGES:
            print('Objective function value was repeated %i times.'%(nochanges))
            break
    return (best_f, best_x)
