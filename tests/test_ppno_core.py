import pytest
import numpy as np
import sys
import os
import logging
from unittest.mock import MagicMock, patch
from ppno.ppno import Optimization, main
from ppno.constants import (
    ALGORITHM_UH, ALGORITHM_DE, ALGORITHM_DA, ALGORITHM_NSGA2, 
    ALGORITHM_MOEAD, ALGORITHM_MACO, ALGORITHM_PSO, ALGORITHM_DIRECT
)

@pytest.fixture
def mock_et():
    with patch('ppno.ppno.et') as m:
        m.ENgetlinkindex.return_value = 1
        m.ENgetnodeindex.return_value = 1
        m.ENgetlinkvalue.return_value = 100.0
        m.ENgetnodevalue.return_value = 25.0
        m.ENopen.return_value = 0
        m.ENopenH.return_value = 0
        m.ENinitH.return_value = 0
        m.ENrunH.return_value = 0
        m.ENnextH.return_value = 0
        m.ENclose.return_value = 0
        m.ENsaveinpfile.return_value = 0
        m.ENreport.return_value = 0
        m.EN_LENGTH = 1
        m.EN_PRESSURE = 11
        m.EN_HEADLOSS = 4
        m.EN_DIAMETER = 0
        m.EN_ROUGHNESS = 1
        yield m

@pytest.fixture
def example_files(tmp_path):
    inp_path = tmp_path / "test.inp"
    inp_path.write_text("Dummy INP")
    ext_path = tmp_path / "test.ext"
    ext_content = (
        "[INP]\ntest.inp\n"
        "[PIPES]\np1 s1\n"
        "[PRESSURES]\nn1 20.0\n"
        "[CATALOG]\ns1 100.0 0.1 10.0\ns1 200.0 0.1 20.0\n"
    )
    ext_path.write_text(ext_content)
    return ext_path, inp_path

def test_init_all_branches(mock_et, tmp_path):
    # 1. Errors (lines 67, 73)
    with pytest.raises(FileNotFoundError): Optimization("ghost.ext")
    ext = tmp_path / "fail.ext"; ext.write_text("[PIPES]\np1 s1\n")
    with pytest.raises(ValueError, match="Mandatory \\[INP\\] section is missing"): Optimization(ext)
    
    # 2. Defensive et call (lines 95-96)
    mock_et.ENsetstatusreport.side_effect = Exception("Fail")
    ext.write_text("[INP]\ntest.inp\n[PIPES]\np1 s1\n[PRESSURES]\nn1 20.0\n[CATALOG]\ns1 100.0 0.1 10.0\n")
    (tmp_path / "test.inp").write_text("")
    Optimization(ext)

def test_options_empty_and_retries(mock_et, tmp_path):
    # Lines 133, 138, 151-152
    ext = tmp_path / "opt.ext"
    ext.write_text("[INP]\ntest.inp\n[OPTIONS]\n \n = \nRETRIES 5\nALGORITHMS DE MACO PSO\n")
    (tmp_path / "test.inp").write_text("")
    opt = Optimization(ext)
    assert opt.max_retries == 5
    assert len(opt.algorithms) == 3

def test_solve_full_logic_coverage(mock_et, example_files):
    opt = Optimization(example_files[0])
    
    # 1. Stage 1 Failure (lines 293-294)
    with patch.object(Optimization, '_solve_uh', return_value=None):
        assert opt.solve() is None
        
    # 2. Stage 2 Combined (Success, Improvement, Failure, Skip)
    opt.algorithms = [ALGORITHM_DE, ALGORITHM_MACO, ALGORITHM_PSO]
    with patch('ppno.scipy_solver.solve_scipy', return_value=np.array([0])), \
         patch('ppno.pygmo_solver.maco', return_value=([0, 0], [1])), \
         patch('ppno.pygmo_solver.nspso', return_value=(None, None)), \
         patch.object(Optimization, 'get_cost', side_effect=[1000, 900, 500, 500, 500, 500, 500, 500, 500]):
        # Initial 1000 -> DE 900 (Improvement 365-366) -> MACO 500 -> PSO Fail (375)
        res = opt.solve()
        assert res is not None
        assert any(r['Algorithm'] == 'MACO' and r['Success'] == 'YES' for r in opt.results)
        assert any(r['Algorithm'] == 'PSO' and r['Success'] == 'NO' for r in opt.results)

    # 3. Stage 2 Skip (line 389)
    opt.algorithms = []
    with patch.object(Optimization, '_solve_uh', return_value=np.array([0])):
        opt.solve()

def test_check_and_print_branches(mock_et, example_files, caplog):
    caplog.set_level(logging.INFO)
    opt = Optimization(example_files[0])
    
    # 1. Deficit tracking in PD (line 248-249)
    mock_et.ENgetnodevalue.return_value = 10.0 # 20 - 10 = 10 deficit
    res = opt.check(mode='PD')
    assert res[0] == 10.0
    
    # 2. Pretty print branches (line 492)
    opt.pretty_print(np.array([0]))
    assert "TOTAL NETWORK COST" in caplog.text

def test_cli_and_errors_final(mock_et, example_files):
    ext_path, _ = example_files
    # 1. CLI Usage (lines 521-522)
    with patch('sys.argv', ['ppno']): 
        with pytest.raises(SystemExit): main()
    with patch('sys.argv', ['ppno', '-h']): 
        with pytest.raises(SystemExit): main()
    
    # 2. Success CLI (line 531)
    with patch('sys.argv', ['ppno', str(ext_path)]), \
         patch.object(Optimization, 'solve', return_value=np.array([0])):
        main()
        
    # 3. Failure CLI (line 535)
    with patch('sys.argv', ['ppno', str(ext_path)]), \
         patch.object(Optimization, 'solve', side_effect=Exception("API Error")):
        with pytest.raises(SystemExit): main()

def test_report_defensive(mock_et, example_files):
    opt = Optimization(example_files[0])
    opt.report_enabled = True
    # Exception inside report loop (line 485)
    mock_et.ENreport.side_effect = Exception("Crash")
    opt._handle_success(np.array([0]))
    assert mock_et.ENsaveinpfile.called
