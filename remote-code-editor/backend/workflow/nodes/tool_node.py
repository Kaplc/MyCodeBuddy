"""Tool 节点"""
from typing import Any, Dict
from django.conf import settings
from services.agent_tools import AgentToolExecutor
from ..utils import run_async, resolve_templates


_tool_executor = AgentToolExecutor(settings.WORKSPACE_PATH)


def tool_node(config: Dict[str, Any]):
    tool_name = config.get('tool') or config.get('name')
    arguments = config.get('arguments', {})

    def run(state: Dict[str, Any]) -> Dict[str, Any]:
        workspace = state.get('workspace')
        if workspace:
            _tool_executor.set_workspace(workspace)

        resolved_args = resolve_templates(arguments, state)
        result = run_async(_tool_executor.execute_tool(tool_name, resolved_args))
        state['result'] = result
        return state

    return run
