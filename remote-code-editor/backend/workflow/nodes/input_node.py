"""Input 节点"""
from typing import Any, Dict


def input_node(config: Dict[str, Any]):
    key = config.get('key', 'input')
    default_value = config.get('value')

    def run(state: Dict[str, Any]) -> Dict[str, Any]:
        if default_value is not None and key not in state:
            state[key] = default_value
        return state

    return run
