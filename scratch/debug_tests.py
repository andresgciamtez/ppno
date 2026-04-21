import numpy as np
from ppno.section_parser import SectionParser
from pathlib import Path
import os

content = """[INP]
test.inp
[OPTIONS]
MAX_RETRIES = 5
MAX_TIME = 600
GENERATE_RPT = YES
[ALGORITHMS]
DE
DA
"""
path = Path("debug.ext")
path.write_text(content)

parser = SectionParser(path)
sections = parser.read()
print(f"Sections: {sections.keys()}")
print(f"OPTIONS: {sections.get('OPTIONS')}")

options_lines = sections.get('OPTIONS', [])
for line in options_lines:
    parts = line.split('=')
    if len(parts) == 2:
        key = parts[0].strip().upper()
        value = parts[1].strip()
        print(f"Key: '{key}', Value: '{value}'")

os.remove(path)

# Test numpy structured array
dt = [('max_hl', 'f4'), ('link_idx', 'i4')]
max_hls = np.zeros(3, dtype=dt)
max_hls[0] = (0.1, 1)
sorted_hls = np.sort(max_hls, order='max_hl')
print(f"Type sorted_hls: {type(sorted_hls)}")
print(f"Shape sorted_hls: {sorted_hls.shape}")
print(f"sorted_hls[0]: {sorted_hls[0]}, type: {type(sorted_hls[0])}")
print(f"sorted_hls[0]['max_hl']: {sorted_hls[0]['max_hl']}")
