import pytest

# Default specifications for testing
TEST_SPECS = {
    "GOLDM": {"quoted_unit_grams": 10, "fineness": 0.995},
    "GOLDTEN": {"quoted_unit_grams": 10, "fineness": 0.999},
    "GOLDGUINEA": {"quoted_unit_grams": 8, "fineness": 0.999},
    "GOLDPETAL": {"quoted_unit_grams": 1, "fineness": 0.999}
}

def test_normalization_formula():
    """
    Test per-gram pure gold calculation:
    Formula = Close / Quote Base / Fineness
    """
    # GOLDM Test: 75000 / 10 / 0.995 = 7537.6884
    close_price = 75000
    spec = TEST_SPECS["GOLDM"]
    norm_price = round(close_price / spec["quoted_unit_grams"] / spec["fineness"], 4)
    
    assert norm_price == 7537.6884

def test_contract_specs_exist():
    """Ensure all 4 contracts exist in specification dictionary"""
    assert "GOLDM" in TEST_SPECS
    assert "GOLDTEN" in TEST_SPECS
    assert "GOLDGUINEA" in TEST_SPECS
    assert "GOLDPETAL" in TEST_SPECS