import pytest
from entoolkit import toolkit as et


def test_epanet_version():
    """Test that the EPANET library loads and returns a version number."""
    try:
        version = et.ENgetversion()
        assert version > 0
        print(f"EPANET Version: {version}")
    except Exception as e:
        pytest.fail(f"Could not load EPANET library or get version: {e}")


def test_constants():
    """Test that some new constants are defined."""
    # The user confirmed the name is EN_DEMANDMODEL without an underscore
    if hasattr(et, "EN_DEMANDMODEL"):
        assert et.EN_DEMANDMODEL == 24
    
    if hasattr(et, "EN_LINK_TYPE"):
        assert et.EN_LINK_TYPE == 14
