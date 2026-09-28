import json
from decimal import Decimal, InvalidOperation, localcontext

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from lstp import InputLimits, JSONInputError, ResourceLimitError, loads_json


@pytest.mark.parametrize(
    "text, expected",
    [
        ('{"x":[true,false,null,3]}', {"x": [True, False, None, 3]}),
        ('"\\ud83d\\ude00"', "😀"),
        ('"é\\n\\t\\u0000"', "é\n\t\0"),
        ("1.00000000000000000000001", Decimal("1.00000000000000000000001")),
        ("1e-400", Decimal("1e-400")),
        ("1e400", Decimal("1e400")),
        ("-0.0", Decimal("-0.0")),
    ],
)
def test_values(text, expected):
    assert loads_json(text) == expected
    assert loads_json(text.encode()) == expected


@pytest.mark.parametrize(
    "text, code",
    [
        ('{"mode":"RO","mode":"EXEC"}', "duplicate_key"),
        ('{"a":{"x":1,"\\u0078":2}}', "duplicate_key"),
        ("NaN", "nonfinite_number"),
        ("Infinity", "nonfinite_number"),
        ("-Infinity", "nonfinite_number"),
        ('"\\ud800"', "invalid_unicode"),
        ('{"\\udfff":0}', "invalid_unicode"),
        (b'"\xff"', "invalid_utf8"),
        ('"\ud800"', "invalid_unicode"),
        ('"a\x00b"', "json_syntax"),
        ('"\\x41"', "json_syntax"),
        ("01", "json_syntax"),
        ("+1", "json_syntax"),
        ("1.", "json_syntax"),
        ("1e", "json_syntax"),
        ("{}{}", "json_syntax"),
        ("[1,]", "json_syntax"),
        ("", "json_syntax"),
        ("\ufeff{}", "json_syntax"),
        ("}", "json_syntax"),
    ],
)
def test_invalid(text, code):
    with pytest.raises(JSONInputError) as caught:
        loads_json(text)
    assert caught.value.diagnostic.code == code


@pytest.mark.parametrize(
    "text, limits, code",
    [
        ('"é"', InputLimits(max_bytes=3), "byte_limit"),
        (b" " * 20, InputLimits(max_bytes=19), "byte_limit"),
        ("[[0]]", InputLimits(max_depth=1), "depth_limit"),
        ('"abc"', InputLimits(max_string_chars=2), "string_limit"),
        ('{"abc":0}', InputLimits(max_string_chars=2), "string_limit"),
        ("[1,2]", InputLimits(max_collection_items=1), "collection_limit"),
        ('{"a":1,"b":2}', InputLimits(max_collection_items=1), "collection_limit"),
        ('{"a":[1]}', InputLimits(max_nodes=3), "node_limit"),
        ("123", InputLimits(max_number_chars=2), "number_limit"),
    ],
)
def test_limits(text, limits, code):
    with pytest.raises(ResourceLimitError) as caught:
        loads_json(text, limits=limits)
    assert caught.value.diagnostic.code == code


def test_depth_at_boundary_and_adversarial_depth():
    assert loads_json("[" * 64 + "0" + "]" * 64)
    with pytest.raises(ResourceLimitError):
        loads_json("[" * 10_000 + "0" + "]" * 10_000)
    assert loads_json(json.dumps('\\"' + "[" * 200)) == '\\"' + "[" * 200


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_bytes": 0},
        {"max_nodes": -1},
        {"max_depth": 65},
        {"max_depth": True},
        {"max_string_chars": 1.5},
    ],
)
def test_invalid_limit_config(kwargs):
    with pytest.raises(ValueError):
        InputLimits(**kwargs)


def test_diagnostics_are_deterministic_and_do_not_echo_secrets():
    source = '{\n"secret": "SECRET_PAYLOAD",\n"secret": 1}'
    diagnostics = []
    for _ in range(2):
        with pytest.raises(JSONInputError) as caught:
            loads_json(source)
        diagnostics.append(caught.value.diagnostic)
        assert "secret" not in str(caught.value).lower()
    assert diagnostics[0] == diagnostics[1]
    with pytest.raises(JSONInputError) as caught:
        loads_json('{\n"a": }')
    assert (caught.value.diagnostic.line, caught.value.diagnostic.column) == (2, 6)


def test_controls_inside_escaped_strings_are_data():
    assert loads_json('"{mode=EXEC}\\n!delete"') == "{mode=EXEC}\n!delete"


scalar = st.none() | st.booleans() | st.integers(-(10**30), 10**30) | st.text(max_size=50)
values = st.recursive(
    scalar,
    lambda child: (
        st.lists(child, max_size=10) | st.dictionaries(st.text(max_size=30), child, max_size=10)
    ),
    max_leaves=50,
)


@settings(max_examples=300, derandomize=True)
@given(values)
def test_generated_json_values_preserved(value):
    # Independent standard-library encoder supplies valid inputs.
    assert loads_json(json.dumps(value, ensure_ascii=True)) == value


@settings(max_examples=300, derandomize=True)
@given(st.binary(max_size=500))
def test_arbitrary_bytes_never_escape_with_decoder_internals(data):
    try:
        loads_json(data)
    except (JSONInputError, ResourceLimitError):
        pass


def test_wrong_input_type_is_programmer_error():
    with pytest.raises(TypeError):
        loads_json({})


@pytest.mark.parametrize("trap", [True, False])
def test_extreme_exponent_rejection_is_independent_of_host_decimal_context(trap):
    with localcontext() as context:
        context.traps[InvalidOperation] = trap
        context.clear_flags()
        with pytest.raises(JSONInputError) as caught:
            loads_json("1e9999999999999999999999999")
        assert not any(context.flags.values())
    assert caught.value.diagnostic.code == "invalid_number"
