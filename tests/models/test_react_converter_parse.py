"""ReactConverter must parse the model's Action as data, never execute it."""

import json

import pytest
from openai.types.responses import ResponseFunctionToolCall

from utu.models.react_converter import ReactConverter


def _call(text: str) -> ResponseFunctionToolCall:
    items = ReactConverter()._parse_react_output(text)
    assert len(items) == 1 and isinstance(items[0], ResponseFunctionToolCall)
    return items[0]


def test_parses_json_action():
    call = _call('Action:\n{"name": "search", "arguments": {"query": "x"}}')
    assert call.name == "search" and json.loads(call.arguments) == {"query": "x"}


def test_parses_python_literal_action():
    call = _call("Action:\n{'name': 'search', 'arguments': {'query': 'smolagents package'}}")
    assert call.name == "search" and json.loads(call.arguments) == {"query": "smolagents package"}


def test_code_in_action_is_not_executed(tmp_path):
    canary = tmp_path / "canary"
    payload = f"__import__('os').system('touch {canary}') or {{'name': 'search', 'arguments': {{'q': 'x'}}}}"
    with pytest.raises(ValueError):
        ReactConverter()._parse_react_output(f"Action:\n{payload}")
    assert not canary.exists()


@pytest.mark.parametrize("action", ["[1, 2]", "{'name': 'search'}", "not a literal"])
def test_rejects_malformed_action(action):
    with pytest.raises(ValueError):
        ReactConverter()._parse_react_output(f"Action:\n{action}")
