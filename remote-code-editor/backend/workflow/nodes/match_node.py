"""Match 节点 - 从 agent 输出中提取匹配的内容"""
from typing import Any, Dict
import re


def match_node(config: Dict[str, Any]):
    """
    Match 节点用于从 agent 输出中提取匹配的内容。
    
    config:
        pattern: 要提取的内容描述，支持正则表达式
        field: 要保存到的字段名，默认为 'matched'
    """
    pattern = config.get('pattern', '')
    field = config.get('field', 'matched')

    def run(state: Dict[str, Any]) -> Dict[str, Any]:
        # 获取上一步的结果
        result = state.get('result', '')
        
        if not result:
            state[field] = ''
            return state
        
        # 如果 pattern 看起来像正则表达式，尝试匹配
        # 否则作为关键字搜索
        try:
            # 尝试作为正则表达式匹配
            match = re.search(pattern, result, re.IGNORECASE | re.DOTALL)
            if match:
                extracted = match.group(0) if match.group(0) else match.group(1) if match.groups() else result
            else:
                # 作为关键字搜索
                if pattern.lower() in result.lower():
                    # 提取包含关键字的部分
                    idx = result.lower().find(pattern.lower())
                    extracted = result[max(0, idx-20):min(len(result), idx+len(pattern)+20)]
                else:
                    extracted = result
        except Exception:
            # 如果正则失败，返回原始结果
            extracted = result
        
        state[field] = extracted
        return state

    return run
