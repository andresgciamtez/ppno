import pytest
from pathlib import Path
from ppno.section_parser import SectionParser


@pytest.fixture
def example_ext_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test.ext"
    content = """[SECTION1]
line1
line2 ; comment
[SECTION2]
val1 val2
[END]
"""
    p.write_text(content)
    return p


def test_read_section(example_ext_file):
    reader = SectionParser(example_ext_file)
    sec1 = reader.read_section("SECTION1")
    assert len(sec1) == 2
    assert sec1[0] == ("line1",)
    assert sec1[1] == ("line2",)


def test_read_all(example_ext_file):
    reader = SectionParser(example_ext_file)
    sections = reader.read()
    assert "SECTION1" in sections
    assert "SECTION2" in sections
    assert sections["SECTION1"] == ["line1", "line2"]
    assert sections["SECTION2"] == ["val1 val2"]


def test_line_to_tuple():
    assert SectionParser.line_to_tuple("a b c") == ("a", "b", "c")


def test_tuple_to_line():
    assert SectionParser.tuple_to_line(("a", "b", "c")) == "a    b    c"
