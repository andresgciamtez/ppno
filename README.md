# PRESSURIZED PIPE NETWORK OPTIMIZER
2019 - Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/

# DEPENDENCIES
Requires:
scipy v1.2
numpy v1.13 (not use version > 1.13)
mumpy-base

# PURPOSE
The program optimizes the pipe diameters of a pressure pipes network defined by an Epanet2 model. The result is the selection of the necessary tubes to meet the minimum pressure requirements in the specified nodes of the network.

# RUN
Type: 'python ppno.py problem.ext' in the command prompt; where 'problem.ext' is the data problem definition file.

# PROBLEM DEFINITION
The file input have a similar structure to an Epanet inp file, it must have extension ext. The sections are indicated by 6 section-headed labels (“[]”). These are: TITLE, INP, OPTIONS, PIPES, PRESSURES and CATALOG. The file ends with the closing line [END]. Apart from the closing line, it is not necessary that the sections have a predetermined order.

The TITLE section allows to include a description of the problem. It is not mandatory, and there are not limitations for the lines of extension in this.
Example:
[TITLE]
Hanoi example by Fujiwara and Khang, Water Resources Research, 1990

The INP section contains the name of the Epanet input file (inp). It must include the full path in the system, unless it is stored in the current path. The use of spaces is not recommended.
Example:
[INP]
C:\my_path\HAN.inp

The OPTIONS section contains the calculation options. Two options must be specified: First, the algorithm trough a line beginning by the word 'Algorithm' followed by a code among:
- 'GD', to select the Gradient Descent;
- 'DE', to select Differential Evolution; and
- 'DA', to select Dual Simulated Annealing.
Secondly, it is possible improve slightly the final solution in small networks by selecting “YES” in a line starting by the word "Polish". Otherwise, “No” must be indicated. 
Example:
[OPTIONS]
Method GD
Polish YES

The PIPES section contains the pipes to be dimensioned according to the identifier "ID", which each one haves in the Epanet model, followed by the series of pipes to be applied. Obviously, it is not necessary to specify all the pipes present in the model. Each pipe in a line.
Example:
[PIPES]
pip1    PVC
pip2    PVC
pip3    FD

The PRESSURES section contains the nodes in which it is necessary to guarantee a minimum pressure. Each node is indicated by its identifier "ID" according to the Epanet model, followed by the minimum pressure. It is not necessary to specify all the nodes of the model.
Example:
[PRESSURES]
nod2    20.0
nod4    20.0
nod7    5.0

 The CATALOG section defines the series of pipes to be used in the sizing. Each line contains the following fields:
- Series, a string that defines each series name;
- diameter, the inside diameter of the pipe;
- roughness, friction factor according to the units specified in the Epanet model; and
- cost, per unit of pipe.
Example:
[CATALOG]
FD   90.0    0.100     1.00
FD  125.0    0.100     1.56
FD  150.0    0.100     1.75
PVC 304.8    0.025    45.73
PVC 406.4    0.025    70.40

It must be considered that it is possible to include different types of material (different roughness) in each series. The zero diameter is equivalent to an eliminate-pipe option. Similarly, a no-substitution-pipe consist in setting the price to 0 in an existing diameter pipe.
In a similar way to the Epanet file, the ";" character is the comment mark, this and all the text follows it on the line will be ignored. Also, lines that contain only spaces or only spaces before the character ";" are ignored.

# RESULTS
The results of the program are shown on the console, and the program returning the dimensioned network in a new Epanet file. The solved file name includes an indicator according to the calculation method used: ‘_Solved_GD’, ‘_Solved_DE’, or ‘_Solved_DA’. 
If a refinement of the final solution is selected, by the polish option, an additional file is generated, which name is included: "+Polish".

# EXAMPLES
Several sample problems are included in the samples folder.

Cuenca, June of 2019
