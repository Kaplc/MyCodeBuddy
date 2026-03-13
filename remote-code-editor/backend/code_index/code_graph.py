"""
代码图结构
存储代码的结构化信息和依赖关系
"""
import os
import ast
import json
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict


@dataclass
class CodeSymbol:
    """代码符号"""
    name: str
    type: str  # function, class, method, variable, import
    file: str
    line: int
    end_line: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent: Optional[str] = None  # 父类或所属模块


@dataclass 
class CodeEdge:
    """代码依赖边"""
    source: str  # 源符号
    target: str  # 目标符号
    type: str    # calls, imports, inherits, uses


class CodeGraph:
    """
    代码图
    
    存储项目中所有代码符号及其关系
    支持快速查询和导航
    """
    
    def __init__(self):
        self.symbols: Dict[str, CodeSymbol] = {}
        self.edges: List[CodeEdge] = []
        self.file_symbols: Dict[str, List[str]] = defaultdict(list)
        self.imports_map: Dict[str, Set[str]] = defaultdict(set)
    
    def add_symbol(self, symbol: CodeSymbol):
        """添加符号"""
        key = f"{symbol.file}::{symbol.name}"
        self.symbols[key] = symbol
        self.file_symbols[symbol.file].append(key)
    
    def add_edge(self, edge: CodeEdge):
        """添加依赖边"""
        self.edges.append(edge)
    
    def get_symbol(self, file: str, name: str) -> Optional[CodeSymbol]:
        """获取符号"""
        key = f"{file}::{name}"
        return self.symbols.get(key)
    
    def get_file_symbols(self, file: str) -> List[CodeSymbol]:
        """获取文件中的所有符号"""
        keys = self.file_symbols.get(file, [])
        return [self.symbols[k] for k in keys if k in self.symbols]
    
    def find_callers(self, symbol_name: str) -> List[str]:
        """查找调用某符号的所有位置"""
        callers = []
        for edge in self.edges:
            if edge.target.endswith(f"::{symbol_name}") and edge.type == "calls":
                callers.append(edge.source)
        return callers
    
    def find_callees(self, symbol_name: str) -> List[str]:
        """查找某符号调用的所有符号"""
        callees = []
        for edge in self.edges:
            if edge.source.endswith(f"::{symbol_name}") and edge.type == "calls":
                callees.append(edge.target)
        return callees
    
    def find_references(self, symbol_name: str) -> List[Dict[str, Any]]:
        """查找符号的所有引用"""
        refs = []
        for edge in self.edges:
            if edge.target.endswith(f"::{symbol_name}"):
                source_symbol = self.symbols.get(edge.source)
                if source_symbol:
                    refs.append({
                        "file": source_symbol.file,
                        "line": source_symbol.line,
                        "type": edge.type
                    })
        return refs
    
    def get_class_hierarchy(self, class_name: str) -> Dict[str, Any]:
        """获取类继承层次"""
        hierarchy = {
            "name": class_name,
            "parents": [],
            "children": []
        }
        
        for edge in self.edges:
            if edge.type == "inherits":
                if edge.source.endswith(f"::{class_name}"):
                    hierarchy["parents"].append(edge.target.split("::")[-1])
                if edge.target.endswith(f"::{class_name}"):
                    hierarchy["children"].append(edge.source.split("::")[-1])
        
        return hierarchy
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbols": {
                k: {
                    "name": v.name,
                    "type": v.type,
                    "file": v.file,
                    "line": v.line,
                    "signature": v.signature,
                    "docstring": v.docstring
                }
                for k, v in self.symbols.items()
            },
            "edges": [
                {"source": e.source, "target": e.target, "type": e.type}
                for e in self.edges
            ],
            "stats": {
                "total_symbols": len(self.symbols),
                "total_edges": len(self.edges),
                "files": len(self.file_symbols)
            }
        }
    
    def save(self, path: str):
        """保存到文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, path: str) -> 'CodeGraph':
        """从文件加载"""
        graph = cls()
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for key, sym_data in data.get("symbols", {}).items():
            graph.symbols[key] = CodeSymbol(
                name=sym_data["name"],
                type=sym_data["type"],
                file=sym_data["file"],
                line=sym_data["line"],
                end_line=sym_data.get("end_line", sym_data["line"]),
                signature=sym_data.get("signature"),
                docstring=sym_data.get("docstring")
            )
            graph.file_symbols[sym_data["file"]].append(key)
        
        for edge_data in data.get("edges", []):
            graph.edges.append(CodeEdge(
                source=edge_data["source"],
                target=edge_data["target"],
                type=edge_data["type"]
            ))
        
        return graph
