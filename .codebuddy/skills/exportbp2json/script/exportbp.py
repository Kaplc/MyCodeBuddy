# exportbp.py
import unreal_engine as ue
import os
import re

def export_assets():
    """UE4.18资源导出功能"""
    ue.log("=== UE资源导出脚本 ===")
    
    exportasset = sys.argv[1]
    if exportasset is None:
        print("资源路径错误")
        exit(-1)
    print(exportasset)
    pattern = r"^(\w+)'([^']+)'$"
    match = re.match(pattern, exportasset)
    exportassettype = None
    exportassetpath = None
    if match:
        exportassettype = match.group(1)  # 类型部分，如 WidgetBlueprint
        exportassetpath = match.group(2)  # 路径部分，如 /Game/UMG/WebViewTestUI.WebViewTestUI
    else:
        # 尝试更宽松的匹配模式
        pattern_loose = r"(\w+)'([^']*)'"
        match_loose = re.search(pattern_loose, exportasset)
        if match_loose:
            exportassettype = match.group(1)  # 类型部分，如 WidgetBlueprint
            exportassetpath = match.group(2)  # 路径部分，如 /Game/UMG/WebViewTestUI.WebViewTestUI
    if exportassetpath is None:
        print("资源路径错误")
        exit(-1)
    if exportassettype is None:
        exportassettype = 'Object'
    exportpath = ue.get_content_dir() + "../Source/Lua/.codebuddy/skills/exportbp2json/script"
    ue.export_assets([ue.load_object(ue.find_class(exportassettype), exportassetpath)], exportpath)
    
    print(f"\n导出完成！文件保存在: {os.path.abspath(exportpath + exportassetpath)}")

if __name__ == "__main__":
    export_assets()