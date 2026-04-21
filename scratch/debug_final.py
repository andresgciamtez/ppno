import re
import numpy as np
from ppno.section_parser import SectionParser
from ppno.local_refiner import LocalRefiner
from unittest.mock import MagicMock

# Test line_to_tuple
line = "a,b,c"
tokens = tuple(word.strip() for word in re.split(r'[\s\t,]+', line) if word.strip())
print(f"Tokens of 'a,b,c': {tokens}")

# Test line_to_tuple via class
res = SectionParser.line_to_tuple(line)
print(f"Res via class: {res}")

# Test local_refiner logic
sim = MagicMock()
sim.get_cost.return_value = 1000.0
sim.check.return_value = True
refiner = LocalRefiner(sim)
x = np.array([0, 0])
promising = refiner.is_promising(x, 1100.0)
print(f"Is [0,0] promising vs 1100? {promising}")
print(f"Evaluation of [0,0]: {refiner.evaluate(x)}")
