"""Output 节点"""
from typing import Any, Dict


def output_node(config: Dict[str, Any]):
    output_key = config.get('output_key')

    def run(state: Dict[str, Any]) -> Dict[str, Any]:
        if output_key:
            state['output'] = state.get(output_key)
        elif 'result' in state:
            state['output'] = state['result']
        return state

    return run
