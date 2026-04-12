"""ENTOOLKIT: A Python Wrapper for the EPANET Programmer's Toolkit.

This module provides a Pythonic interface to the EPANET 2.x C library using ctypes.
It handles library loading for Windows, Linux, and macOS.
"""

import ctypes
import platform
import sys
from pathlib import Path
from typing import Tuple, List, Optional, Callable, Union, Any

# --- Library Loading ---

_OS_NAME = platform.system()
_MACHINE = platform.machine()
_BASE_PATH = Path(__file__).parent / "epanet"

if _OS_NAME == "Windows":
    _dll_name = "epanet2_amd64.dll" if "64" in _MACHINE else "epanet2.dll"
    _lib_path = _BASE_PATH / "Windows" / _dll_name
    # Using WinDLL for __stdcall convention on Windows
    _lib = ctypes.WinDLL(str(_lib_path))
elif _OS_NAME == "Darwin":
    _lib_path = _BASE_PATH / "Darwin" / "libepanet2.dylib"
    _lib = ctypes.CDLL(str(_lib_path))
else:
    _lib_path = _BASE_PATH / "Linux" / "libepanet.so"
    _lib = ctypes.CDLL(str(_lib_path))

# --- General Constants ---

MAX_LABEL_LEN = 15
ERR_MAX_CHAR = 80


class ENtoolkitError(Exception):
    """Exception raised for errors in the EPANET Toolkit.

    Attributes:
        ierr (int): The error code returned by the toolkit.
        warning (bool): True if the code represents a warning (< 100).
        message (str): Descriptive error message.
    """

    def __init__(self, ierr: int):
        self.ierr = ierr
        self.warning = ierr < 100
        self.message = ENgeterror(ierr)
        if not self.message and ierr:
            self.message = f"ENtoolkit Undocumented Error {ierr}: check EPANET documentation/headers"

    def __str__(self) -> str:
        return self.message


# --- API Functions ---

def ENepanet(inp_file: str, rpt_file: str = '', bin_file: str = '', 
             vfunc: Optional[Callable[[str], None]] = None) -> None:
    """Runs a complete EPANET simulation.

    Args:
        inp_file: Path to the input file (.inp).
        rpt_file: Path to the report file (.rpt).
        bin_file: Path to the optional binary output file.
        vfunc: Optional callback function that accepts a status string.
    """
    callback = None
    if vfunc is not None:
        cfunc = ctypes.CFUNCTYPE(None, ctypes.c_char_p)
        callback = cfunc(lambda msg: vfunc(msg.decode()))
        
    ierr = _lib.ENepanet(ctypes.c_char_p(inp_file.encode()),
                         ctypes.c_char_p(rpt_file.encode()),
                         ctypes.c_char_p(bin_file.encode()),
                         callback)
    if ierr:
        raise ENtoolkitError(ierr)


def ENopen(inp_file: str, rpt_file: str = '', bin_file: str = '') -> None:
    """Opens an EPANET project for analysis."""
    ierr = _lib.ENopen(ctypes.c_char_p(inp_file.encode()),
                       ctypes.c_char_p(rpt_file.encode()),
                       ctypes.c_char_p(bin_file.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def ENclose() -> None:
    """Closes the EPANET toolkit and releases files."""
    ierr = _lib.ENclose()
    if ierr:
        raise ENtoolkitError(ierr)


def ENgetnodeindex(node_id: str) -> int:
    """Gets the index of a node from its ID string."""
    index_ptr = ctypes.c_int()
    ierr = _lib.ENgetnodeindex(ctypes.c_char_p(node_id.encode()), ctypes.byref(index_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return index_ptr.value


def ENgetnodeid(index: int) -> str:
    """Gets the ID string of a node from its index."""
    id_buffer = ctypes.create_string_buffer(MAX_LABEL_LEN + 1)
    ierr = _lib.ENgetnodeid(index, ctypes.byref(id_buffer))
    if ierr:
        raise ENtoolkitError(ierr)
    return id_buffer.value.decode()


def ENgetnodetype(index: int) -> int:
    """Gets the type code for a node."""
    type_ptr = ctypes.c_int()
    ierr = _lib.ENgetnodetype(index, ctypes.byref(type_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return type_ptr.value


def ENgetnodevalue(index: int, param_code: int) -> float:
    """Gets the value of a specific node parameter."""
    value_ptr = ctypes.c_float()
    ierr = _lib.ENgetnodevalue(index, param_code, ctypes.byref(value_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return float(value_ptr.value)


def ENsetnodevalue(index: int, param_code: int, value: float) -> None:
    """Sets the value of a specific node parameter."""
    ierr = _lib.ENsetnodevalue(index, param_code, ctypes.c_float(value))
    if ierr:
        raise ENtoolkitError(ierr)


def ENgetlinkindex(link_id: str) -> int:
    """Gets the index of a link from its ID string."""
    index_ptr = ctypes.c_int()
    ierr = _lib.ENgetlinkindex(ctypes.c_char_p(link_id.encode()), ctypes.byref(index_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return index_ptr.value


def ENgetlinkid(index: int) -> str:
    """Gets the ID string of a link from its index."""
    id_buffer = ctypes.create_string_buffer(MAX_LABEL_LEN + 1)
    ierr = _lib.ENgetlinkid(index, ctypes.byref(id_buffer))
    if ierr:
        raise ENtoolkitError(ierr)
    return id_buffer.value.decode()


def ENgetlinktype(index: int) -> int:
    """Gets the type code for a link."""
    type_ptr = ctypes.c_int()
    ierr = _lib.ENgetlinktype(index, ctypes.byref(type_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return type_ptr.value


def ENgetlinknodes(index: int) -> Tuple[int, int]:
    """Gets the indexes of the start and end nodes of a link."""
    from_node_ptr = ctypes.c_int()
    to_node_ptr = ctypes.c_int()
    ierr = _lib.ENgetlinknodes(index, ctypes.byref(from_node_ptr), ctypes.byref(to_node_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return from_node_ptr.value, to_node_ptr.value


def ENgetlinkvalue(index: int, param_code: int) -> float:
    """Gets the value of a specific link parameter."""
    value_ptr = ctypes.c_float()
    ierr = _lib.ENgetlinkvalue(index, param_code, ctypes.byref(value_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return float(value_ptr.value)


def ENsetlinkvalue(index: int, param_code: int, value: float) -> None:
    """Sets the value of a specific link parameter."""
    ierr = _lib.ENsetlinkvalue(index, param_code, ctypes.c_float(value))
    if ierr:
        raise ENtoolkitError(ierr)


def ENgetpatternid(index: int) -> str:
    """Gets the ID string of a time pattern."""
    id_buffer = ctypes.create_string_buffer(MAX_LABEL_LEN + 1)
    ierr = _lib.ENgetpatternid(index, ctypes.byref(id_buffer))
    if ierr:
        raise ENtoolkitError(ierr)
    return id_buffer.value.decode()


def ENgetpatternindex(pattern_id: str) -> int:
    """Gets the index of a time pattern from its ID."""
    index_ptr = ctypes.c_int()
    ierr = _lib.ENgetpatternindex(ctypes.c_char_p(pattern_id.encode()), ctypes.byref(index_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return index_ptr.value


def ENgetpatternlen(index: int) -> int:
    """Gets the number of periods in a time pattern."""
    len_ptr = ctypes.c_int()
    ierr = _lib.ENgetpatternlen(index, ctypes.byref(len_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return len_ptr.value


def ENgetpatternvalue(index: int, period: int) -> float:
    """Gets the multiplier for a specific pattern period."""
    value_ptr = ctypes.c_float()
    ierr = _lib.ENgetpatternvalue(index, period, ctypes.byref(value_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return float(value_ptr.value)


def ENsetpattern(index: int, factors: List[float]) -> None:
    """Sets all multipliers for a specific pattern."""
    num_factors = len(factors)
    cfactors = (ctypes.c_float * num_factors)(*factors)
    ierr = _lib.ENsetpattern(index, cfactors, num_factors)
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetpatternvalue(index: int, period: int, value: float) -> None:
    """Sets the multiplier for a specific pattern period."""
    ierr = _lib.ENsetpatternvalue(index, period, ctypes.c_float(value))
    if ierr:
        raise ENtoolkitError(ierr)


def ENgetcount(count_code: int) -> int:
    """Gets the number of components of a certain type."""
    count_ptr = ctypes.c_int()
    ierr = _lib.ENgetcount(count_code, ctypes.byref(count_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return count_ptr.value


def ENgetflowunits() -> int:
    """Gets the flow units code for the project."""
    units_ptr = ctypes.c_int()
    ierr = _lib.ENgetflowunits(ctypes.byref(units_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return units_ptr.value


def ENgettimeparam(param_code: int) -> int:
    """Gets the value of a specific time parameter."""
    time_ptr = ctypes.c_int()
    ierr = _lib.ENgettimeparam(param_code, ctypes.byref(time_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return time_ptr.value


def ENsettimeparam(param_code: int, time_value: int) -> None:
    """Sets the value of a specific time parameter."""
    ierr = _lib.ENsettimeparam(param_code, time_value)
    if ierr:
        raise ENtoolkitError(ierr)


def ENgetqualtype(qual_code_out: Any = None, trace_node_out: Any = None) -> Tuple[int, int]:
    """Gets the type of water quality analysis and trace node."""
    q_ptr = ctypes.c_int()
    t_ptr = ctypes.c_int()
    ierr = _lib.ENgetqualtype(ctypes.byref(q_ptr), ctypes.byref(t_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return q_ptr.value, t_ptr.value


def ENsetqualtype(qual_code: int, chem_name: str, chem_units: str, trace_node: str) -> None:
    """Sets the water quality analysis parameters."""
    ierr = _lib.ENsetqualtype(qual_code,
                              ctypes.c_char_p(chem_name.encode()),
                              ctypes.c_char_p(chem_units.encode()),
                              ctypes.c_char_p(trace_node.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def ENgetoption(option_code: int) -> float:
    """Gets the value of a simulation option."""
    value_ptr = ctypes.c_float()
    ierr = _lib.ENgetoption(option_code, ctypes.byref(value_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return float(value_ptr.value)


def ENsetoption(option_code: int, value: float) -> None:
    """Sets the value of a simulation option."""
    ierr = _lib.ENsetoption(option_code, ctypes.c_float(value))
    if ierr:
        raise ENtoolkitError(ierr)


def ENgetversion() -> int:
    """Gets the version number of the EPANET toolkit."""
    version_ptr = ctypes.c_int()
    ierr = _lib.ENgetversion(ctypes.byref(version_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return version_ptr.value


def ENsolveH() -> None:
    """Solves the hydraulics for the current project."""
    ierr = _lib.ENsolveH()
    if ierr:
        raise ENtoolkitError(ierr)


def ENopenH() -> None:
    """Opens the hydraulic solver."""
    ierr = _lib.ENopenH()
    if ierr:
        raise ENtoolkitError(ierr)


def ENinitH(init_flag: int = 0) -> None:
    """Initializes the hydraulic solver."""
    ierr = _lib.ENinitH(init_flag)
    if ierr:
        raise ENtoolkitError(ierr)


def ENrunH() -> int:
    """Executes a single step of the hydraulic simulation. Returns simulation time."""
    time_ptr = ctypes.c_long()
    ierr = _lib.ENrunH(ctypes.byref(time_ptr))
    if ierr >= 100:
        raise ENtoolkitError(ierr)
    return time_ptr.value


def ENnextH() -> int:
    """Advances one time step in the simulation. Returns time remaining."""
    deltat_ptr = ctypes.c_long()
    ierr = _lib.ENnextH(ctypes.byref(deltat_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return deltat_ptr.value


def ENcloseH() -> None:
    """Closes the hydraulic solver."""
    ierr = _lib.ENcloseH()
    if ierr:
        raise ENtoolkitError(ierr)


def ENsolveQ() -> None:
    """Solves water quality for current project."""
    ierr = _lib.ENsolveQ()
    if ierr:
        raise ENtoolkitError(ierr)


def ENopenQ() -> None:
    """Opens the quality solver."""
    ierr = _lib.ENopenQ()
    if ierr:
        raise ENtoolkitError(ierr)


def ENinitQ(init_flag: int = 0) -> None:
    """Initializes the quality solver."""
    ierr = _lib.ENinitQ(init_flag)
    if ierr:
        raise ENtoolkitError(ierr)


def ENrunQ() -> int:
    """Runs one quality simulation step. Returns time."""
    time_ptr = ctypes.c_long()
    ierr = _lib.ENrunQ(ctypes.byref(time_ptr))
    if ierr >= 100:
        raise ENtoolkitError(ierr)
    return time_ptr.value


def ENnextQ() -> int:
    """Advances one quality simulation step. Returns time remaining."""
    deltat_ptr = ctypes.c_long()
    ierr = _lib.ENnextQ(ctypes.byref(deltat_ptr))
    if ierr:
        raise ENtoolkitError(ierr)
    return deltat_ptr.value


def ENcloseQ() -> None:
    """Closes quality solver."""
    ierr = _lib.ENcloseQ()
    if ierr:
        raise ENtoolkitError(ierr)


def ENsaveH() -> None:
    """Saves hydraulic results."""
    ierr = _lib.ENsaveH()
    if ierr:
        raise ENtoolkitError(ierr)


def ENsaveinpfile(file_name: str) -> None:
    """Saves current network state as an .inp file."""
    ierr = _lib.ENsaveinpfile(ctypes.c_char_p(file_name.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsavehydfile(file_name: str) -> None:
    """Saves binary hydraulics results."""
    ierr = _lib.ENsavehydfile(ctypes.c_char_p(file_name.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def ENusehydfile(file_name: str) -> None:
    """Uses a pre-calculated hydraulics binary file."""
    ierr = _lib.ENusehydfile(ctypes.c_char_p(file_name.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def ENreport() -> None:
    """Generates the report file."""
    ierr = _lib.ENreport()
    if ierr:
        raise ENtoolkitError(ierr)


def ENresetreport() -> None:
    """Resets all report commands."""
    ierr = _lib.ENresetreport()
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetreport(command: str) -> None:
    """Applies a specific report configuration command."""
    ierr = _lib.ENsetreport(ctypes.c_char_p(command.encode()))
    if ierr:
        raise ENtoolkitError(ierr)


def ENsetstatusreport(status_level: int) -> None:
    """Sets the level of status reporting (0, 1, or 2)."""
    ierr = _lib.ENsetstatusreport(status_level)
    if ierr:
        raise ENtoolkitError(ierr)


def ENgeterror(error_code: int) -> str:
    """Converts a toolkit error code to a readable message string."""
    error_msg = ctypes.create_string_buffer(ERR_MAX_CHAR)
    _lib.ENgeterror(error_code, ctypes.byref(error_msg), ERR_MAX_CHAR)
    return error_msg.value.decode()


# --- EPANET Constant Definitions ---

# Node Parameters
EN_ELEVATION     = 0
EN_BASEDEMAND    = 1
EN_PATTERN       = 2
EN_EMITTER       = 3
EN_INITQUAL      = 4
EN_SOURCEQUAL    = 5
EN_SOURCEPAT     = 6
EN_SOURCETYPE    = 7
EN_TANKLEVEL     = 8
EN_DEMAND        = 9
EN_HEAD          = 10
EN_PRESSURE      = 11
EN_QUALITY       = 12
EN_SOURCEMASS    = 13
EN_INITVOLUME    = 14
EN_MIXMODEL      = 15
EN_MIXZONEVOL    = 16
EN_TANKDIAM      = 17
EN_MINVOLUME     = 18
EN_VOLCURVE      = 19
EN_MINLEVEL      = 20
EN_MAXLEVEL      = 21
EN_MIXFRACTION   = 22
EN_TANK_KBULK    = 23
# EPANET 2.2 additional node parameters
EN_DEMAND_MODEL  = 24
EN_PDD_MIN_P     = 25
EN_PDD_NOM_P     = 26
EN_PDD_EXP       = 27

# Link Parameters
EN_DIAMETER      = 0
EN_LENGTH        = 1
EN_ROUGHNESS     = 2
EN_MINORLOSS     = 3
EN_INITSTATUS    = 4
EN_INITSETTING   = 5
EN_KBULK         = 6
EN_KWALL         = 7
EN_FLOW          = 8
EN_VELOCITY      = 9
EN_HEADLOSS      = 10
EN_STATUS        = 11
EN_SETTING       = 12
EN_ENERGY        = 13
# EPANET 2.2 additional link parameters
EN_LINK_TYPE     = 14

# Time Parameters
EN_DURATION      = 0
EN_HYDSTEP       = 1
EN_QUALSTEP      = 2
EN_PATTERNSTEP   = 3
EN_PATTERNSTART  = 4
EN_REPORTSTEP    = 5
EN_REPORTSTART   = 6
EN_RULESTEP      = 7
EN_STATISTIC     = 8
EN_PERIODS       = 9

# Component Counts
EN_NODECOUNT     = 0
EN_TANKCOUNT     = 1
EN_LINKCOUNT     = 2
EN_PATCOUNT      = 3
EN_CURVECOUNT    = 4
EN_CONTROLCOUNT  = 5

# Node Types
EN_JUNCTION      = 0
EN_RESERVOIR     = 1
EN_TANK          = 2

# Link Types
EN_CVPIPE        = 0
EN_PIPE          = 1
EN_PUMP          = 2
EN_PRV           = 3
EN_PSV           = 4
EN_PBV           = 5
EN_FCV           = 6
EN_TCV           = 7
EN_GPV           = 8

# Flow Units
EN_CFS           = 0
EN_GPM           = 1
EN_MGD           = 2
EN_IMGD          = 3
EN_AFD           = 4
EN_LPS           = 5
EN_LPM           = 6
EN_MLD           = 7
EN_CMH           = 8
EN_CMD           = 9

# Simulation Options
EN_TRIALS        = 0
EN_ACCURACY      = 1
EN_TOLERANCE     = 2
EN_EMITEXPON     = 3
EN_DEMANDMULT    = 4
# EPANET 2.2 additional options
EN_HEADLOSSFORM  = 5

# Control Types
EN_LOWLEVEL      = 0
EN_HILEVEL       = 1
EN_TIMER         = 2
EN_TIMEOFDAY     = 3

# Flags and Status levels
EN_NOSAVE        = 0
EN_SAVE          = 1
EN_INITFLOW      = 10
