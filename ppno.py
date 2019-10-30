# -*- coding: utf-8 -*-
"""PRESSURIZED PIPE NETWORK OPTIMIZER
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from sys import argv
from time import perf_counter, localtime, strftime
import numpy as np   
import toolkit as et
import htxt as ht

A_GD = 0
A_DE = 1
A_DA = 2
A_NSGA2 = 3
PENALTY = 1e24

class Ppn():
    '''Base class for a presurized pipe network optimization problem    
    
    inpfn: str, definition problem file name (.ext)
    '''   
    def __init__(self, problemfn):
        '''problemfn: file name 
            definition problem file name'''
        # READ PROBLEM FILE NAME
        self.problemfn = problemfn
        myht = ht.Htxtf(problemfn)
        sections = myht.read()
        
        # READ EPANET MODEL INP FILE
        self.inpfn = sections['INP'][0]
        
        # OPEN EPANET MODEL AND HYDRAULIC MODEL
        et.ENopen(self.inpfn, self.inpfn[:-4]+'.rpt')
        et.ENopenH()
        print('-'*80)
        print('DATA')
        print('Network: %s' %(self.inpfn))
        
        # READ OPTIONS
        msg = 'The algorithm selected is: '
        for line in sections['OPTIONS']:
            key,value = myht.line_to_tuple(line)
            if key.upper() == 'ALGORITHM':
                if value == 'GD':
                    self.algorithm = A_GD
                    msg += 'Gradient Descent.'
                elif value == 'DE':
                    self.algorithm = A_DE
                    msg += 'Differential Evolution.'
                elif value == 'DA':
                    self.algorithm = A_DA
                    msg += 'Dual Annaeling.'
                elif value == 'NSGA2':
                    self.algorithm = A_NSGA2
                    msg += 'NSGA-II.'
                    
            elif key.upper() == 'POLISH':
                if value.upper() in ['YES', 'Y']:
                    self.polish = True
                    msg += ' A final polish was selected.'
                else:
                    self.polish = False
                    msg += ' A final polish was not selected.'
           
        print(msg)
        
        # READ PIPES
        # pipes: numpy array of labeled tuples ('ix','id','length','series'), where
        # ix: int, epanet pipe index
        # id: str, epanet pipe ID
        # length: float, epaneht pipe lenghth
        # series: str, pipe series in catalog
        dt=np.dtype([('ix','i4'),('id','U16'),('length','f4'),('series','U16')])
        tmp = []
        for line in sections['PIPES']:
            ide,series = myht.line_to_tuple(line)
            ix = et.ENgetlinkindex(ide)
            l = et.ENgetlinkvalue(ix,et.EN_LENGTH)
            tmp.append((ix,ide,l,series))
        self.pipes = np.array(tmp,dt)
        print('%i pipe/s to size was/were loaded.' %(len(self.pipes)))
        
        # READ PRESSURES
        # nodes: numpy array of labeled tuples ('ix','id','pressure'), where
        # ix: int, epanet node index
        # id: str, epanet node ID
        # pressure: float, min pressure required
        dt = np.dtype([('ix','i4'),('id','U16'),('pressure','f4')])
        tmp = []
        for line in sections['PRESSURES']:
            ide,p = myht.line_to_tuple(line)
            ix = (et.ENgetnodeindex(ide))
            tmp.append((ix,ide,p))
        self.nodes = np.array(tmp, dtype = dt)
        print('%i node/s to check was/were loaded.' %(len(self.nodes)))
        
        # READ CATALOG
        dt = np.dtype([('diameter','f4'),('roughness','f4'),('price','f4')])
        self.catalog = {}
        tmp = set()
        for pipe in np.nditer(self.pipes):
            tmp.add(str(pipe['series']))
        print('%i series/s was/were required.'%(len(tmp)), end='')
        for seriesname in tmp:
            self.catalog[seriesname] = []
        for line in sections['CATALOG']:
            sn,d,r,p = myht.line_to_tuple(line)
            if sn in tmp:
                self.catalog[sn].append((d,r,p)) 
        # READ SERIES
        # catalog: dictionary of series {'series' : series}, where
        # series: numpy array of labeled numpy tuples ('diameter','roughness','price'), 
        # where
        # diameter: float, pipe diameter
        # roughness: float, pipe roughness
        # price: float, pipe price
        for series in self.catalog:
            tmp = self.catalog[series].copy()
            self.catalog[series] = np.array(tmp, dtype = dt)
            self.catalog[series].sort()
        print(' %i series/s was/were loaded.' %(len(self.catalog)))  
        
        # DEFINE VARIABLE, DIMENSION AND BOUNDS
        self.dimension = len(self.pipes)
        self._x = np.zeros(self.dimension, dtype=np.int)
        tmp = []
        for pipe in self.pipes:
            tmp.append(len(self.catalog[pipe['series']])-1)
        self.lbound = np.zeros(self.dimension, dtype=np.int)
        self.ubound = np.array(tmp, dtype=np.int)
        print('-'*80)
               
    def set_x(self, x):
        '''Set x updating the hydraulic model
        
        x: numpy array of integers containing the size of the pipes, where
            size: int, index of series in catalog. 
        '''
        self._x = x
        self._update()
        
    def get_x(self):
        '''Return x
        
        '''
        return self._x
    
    def _update(self):
        '''Update pipe diameter and roughness in the epanet model
        '''
        for index,pipe in np.ndenumerate(self.pipes):
            ix = pipe['ix']
            series = self.catalog[pipe['series']]
            size = int(self._x[index])
            d = series[size]['diameter']
            r = series[size]['roughness']
            et.ENsetlinkvalue(ix,et.EN_DIAMETER,d)
            et.ENsetlinkvalue(ix,et.EN_ROUGHNESS,r)
    
    def check(self, mode='TF'):
        '''Run a check of the pressures in the epanet model      
        
        mode: str, can be: 'TF', 'GD', 'PD' 
        
        Return
        ------
        Accordig to mode, returns:
            'TF', status: boolean, calculated pressures are not lower than required 
            
            'GD', (status,headlosses): tuple, where
                headlosses: numpy descend ordered array by headloss pipe index 
                where index: int, is the index of pipe in pipes (not epanet ix).
                
            'PD', deficits: numpy array. Nodal pressure deficits, where
                deficit: float, = required presure - calculated pressure;
                array index corresponds with node in nodes (not epanet ix).        
        '''
        # DEFINE NUMPY ARRAYS
        if mode=='PD':
            deficits=np.array([np.inf for node in self.nodes],dtype=np.float32)
        if mode=='GD':
            dt = np.dtype([('index','i4'),('hl','f4')])
            pipehls=np.array([(i, 0.0) for i in range(len(self.pipes))],dtype=dt)
        
        # SOLVE HYDRAULIC MODEL
        status = True
        et.ENinitH(0)
        while True:
            # RUN A STEP
            et.ENrunH()
            # CHECK PRESSURES IN NODES
            for index,node in  np.ndenumerate(self.nodes):
                ix = int(node['ix'])
                cp = et.ENgetnodevalue(ix,et.EN_PRESSURE)
                rp = node['pressure']
                nodaldeficit = rp - cp 
                if nodaldeficit > 0:
                    status = False
                    # NOT NECCESSARY RETURN HEADLOSS OR PRESSURE SO EXIT
                    if mode == 'TF':
                        return status
                
                # UPDATE DEFICIT ARRAY
                if mode == 'PD':
                    if deficits[index] > nodaldeficit:
                       deficits[index] = nodaldeficit 
            
            # CALCULATE MAXIMUM UNITARY HEADLOSS ARRAY
            if mode == 'GD':
                for pipe in np.nditer(pipehls):
                    index = pipe['index']
                    ix = int(self.pipes[pipe['index']]['ix'])
                    hl = et.ENgetlinkvalue(ix,et.EN_HEADLOSS)
                    if pipehls[index]['hl'] < hl:
                       pipehls[index]['hl'] = hl
            
            # END OF SIMULATON
            if et.ENnextH() ==0:
                break
    
        # SORT HEADLOSS PIPES
        if mode == 'GD':
            tmp = np.sort(pipehls, order='hl')[::-1]
            headlosses = np.array(tmp[:]['index'], dtype=np.int)
        
        # RESULT
        if mode == 'TF':
            return status
        elif mode == 'GD':
            return (status,headlosses)
        elif mode == 'PD':
            return deficits
    
    def save_file(self,fn):
        '''Save inp file updating d and roughness'''
        # UPDATE AND SAVE MODEL
        et.ENsaveinpfile(fn)
    
    def get_cost(self):
        '''Return the network cost. Sum of length x price for each pipe'''
        acumulate = 0.0
        x = self.get_x()
        for index,pipe in np.ndenumerate(self.pipes):
            l = pipe['length']
            p = self.catalog[pipe['series']][x[index]]['price']
            acumulate += l*p
        return acumulate
    
    # SOLVER
    def solve(self): 
        '''Run the optimization of the pressurized pipe network
        
        Return
        ------
        The best solution found , where
            solution: numpy int array, sizes of pipes, according to series.
        
        If no solution is found return None. 
            
        The optimized epanet model is saved in a new file.
        '''
        startime = perf_counter()
        solution = None
        reducted = False
        print('SOLVING')
        print('The solver started at: ' + strftime("%H:%M:%S", localtime()))      
                
        # SELECT ALGORITHM          
        if self.algorithm == A_GD:
            # GRADIENT DESCENT ALGORITHM 
            print('*** GRADIENT DESCENT ALGORITHM ***')

            # SET TO 0 AND INITIAL PRESSURE CHECKING
            self.set_x(np.zeros(self.dimension, dtype=np.int))
            
            while True:
                # CHECK PRESSURES
                status,headlosses = self.check(mode='GD')
                if status:
                    # PRESSURES OK END OF LOOP
                    break

                # INCREASE DIAMETER
                for index in np.nditer(headlosses):               
                    x = self.get_x()
                    if x[index] < self.ubound[index]:
                        x[index] += 1
                        self.set_x(x)
                        break
            
            if status:
                solution = self.get_x().copy()
                        
        if self.algorithm in [A_DE, A_DA]:
            # DIFFEERENTIAL EVOLUTION / DUAL ANNEALING ALGORITHM
            # SET BOUNDS
            tmp = list(zip(self.lbound,self.ubound))
            self.bounds = np.array(tmp, dtype = np.int)
            def objetive(x):
                self.set_x(np.array([round(i) for i in x[:]], np.int))
                if self.check(mode='TF'):
                    return self.get_cost()
                else:
                    return PENALTY

            # SOLVE
            if self.algorithm == A_DE:
                # DIFFEERENTIAL EVOLUTION
                from scipy.optimize import differential_evolution
                print('*** DIFFERENTIAL EVOLUTION ALGORITHM ***')
                result = differential_evolution(objetive, self.bounds)
            else:
                # DUAL ANNEALING ALGORITHM
                from scipy.optimize import dual_annealing
                print('*** DUAL ANNEALING ALGORITHM ***')    
                result = dual_annealing(objetive, self.bounds)
            
            # CHECK
            tmp = [round(i) for i in result.x[:]]
            tmp = np.array(tmp, dtype=np.int)
            self.set_x(tmp)
            if self.check(mode='TF'):
                solution = self.get_x().copy()
            else:
                solution = None           
       
        if self.algorithm == A_NSGA2:
            # NSGA-II
            from gaoptimizer import nsga2
            tmp = nsga2(self)[1]
            if type(tmp) != type(None):
                solution = np.array(tmp,np.int)
                
        if self.polish and (type(solution) != type(None)):
            # POLISH ALGORITHM    
            maxredxset = [0.0,[]]
            def search_reduc(savings, redxset):
                '''
                Searh possible reduction of pipe diameters
                
                redxset: list of ordered by index pipe-set which diameter can 
                    be reduced 1-step according to pipe series.
                
                savings: reduction of cost reached applying redxset
                
                If a pipe can be reduced, it is added, starting a recursively
                precces that stop when no pipe can be reduced, then the reduction
                cost is compared whith previous max reduccion, updating it.
                     
                Return
                ------
                Update maxredset 
                '''
                changes = False
                # SET TO SOL - REDUCTIONS
                newx = solution.copy()
                
                if len(redxset) > 0:
                    start = redxset[-1]
                else:
                    start = 0
                for i in redxset[:]:
                    newx[i] -=1
                # SEARCH FOR A POSSIBLE REDUCIBLE PIPE 
                for i in range(start,len(self._x)): 
                    if  newx[i] > 0:
                        # REDUCE DIAMETER
                        newx[i] -= 1
                        # CHECK PRESSURES
                        self.set_x(newx)
                        if self.check(mode='TF'):
                            # ACEPPT CHANGES
                            changes = True
                            series = self.catalog[self.pipes[i]['series']] 
                            c1 = series[newx[i]+1]['price']
                            c2 = series[newx[i]]['price']
                            l = self.pipes[i]['length']
                            newsavings = savings+(c1-c2)*l
                            newredxset = redxset.copy()
                            newredxset.append(i)
                            search_reduc(newsavings, newredxset) 
                        else:
                            # UNDO
                            newx[i] += 1
                if not changes:
                    # CHECK AND UPDATE MAX REDUCTION SET
                    if savings > maxredxset[0]:
                        maxredxset[0] = savings
                        maxredxset[1] = redxset
            
            print('+++ POLISH ALGORITHM +++')
            search_reduc(0.0, [])            
            print('The maximum reduction cost is: %.2f'%(maxredxset[0]))
            if maxredxset[0] > 0:
                reducted = True
                for i in maxredxset[1][:]:
                    solution[i] -=1
                
        # SOLUTION
        if type(solution) != type(None):
            print('Solving was successful.')
            self.set_x(solution)                
            cost = self.get_cost()
            print('Network cost is: %.2f'%(cost))
            solvedfn = self.inpfn[:-4]+'_Solved_'
            if self.algorithm == A_GD:    
                solvedfn += 'GD'
            elif self.algorithm == A_DE:
                solvedfn += 'DE'
            elif self.algorithm == A_DA:
                solvedfn += 'DA'
            elif self.algorithm == A_NSGA2:
                solvedfn += 'NSGA2'
            if reducted:
                solvedfn += '+Polish.inp'
            else:
                solvedfn += '.inp'
            self.save_file(solvedfn)
            print('Sized network saved in: %s'%(solvedfn))
        else:
            print('No solution found.')
        
        # DURATION
        print('Finished at:', strftime("%H:%M:%S"),end = '')
        print('. Duration = ',perf_counter()-startime)
        print('-'*80)
        
        return solution

    def pretty_print(self, x):
        '''Print the solution in a readable format'''
        # PRINT SOLUTION
        cost = 0
        print('*** SOLUTION ***')
        print('-'*80)
        m = '{:>16} {:>16} {:>8} {:>9} {:>6} {:>6} {:>10}'.format(   \
                                   'Epanet Pipe ID', 'series name', 'diameter',\
                                   'roughness', 'length', 'price', 'amount')
        print(m)
        print('-'*80)
        for i in range(len(self.pipes)):
            ide = self.pipes[i]['id']
            series = self.pipes[i]['series']
            size = int(x[i])
            d = self.catalog[series][size]['diameter']
            r = self.catalog[series][size]['roughness']
            p = self.catalog[series][size]['price']
            l = self.pipes[i]['length']
            a = p * l
            cost += a
            m='{:>16} {:>16} {:8.1f} {:9.4f} {:6.1f} {:6.2f} {:10.2f}'.format(\
                                                     ide, series, d, r, l, p, a)
            print(m)
        print('-'*80)
        print('Total cost: {:10.2f}'.format(cost))
        print('='*80)
  
def main(argv):
    #RUN AN OPTIMIZATION
    print('*'*80)
    print('PRESSURIZED PIPE NETWORK OPTIMIZER')
    print('v0.1', 'ppnoptimizer@gmail.com')
    print('Licensed under the Apache License 2.0. http://www.apache.org/licenses/')
    print('*'*80)

    # LOAD PROBLEM
    myopt = Ppn(argv[1])
    # SOLVE
    solution = myopt.solve()
    # PRINT SOLUTION
    if type(solution) != type(None):
        myopt.pretty_print(solution)

if __name__== "__main__":
    main(argv[:])
