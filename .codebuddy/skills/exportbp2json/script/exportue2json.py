import json
import re
import os
import sys

def parse_ue_blueprint_file(input_file_path):
    """从文件路径读取Unreal Engine蓝图TXT文件并转换为JSON"""
    # 读取文件内容
    with open(input_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    def parse_object(lines, start_index):
        """解析一个完整的Begin Object到End Object块"""
        if start_index >= len(lines) or not lines[start_index].strip().startswith('Begin Object'):
            return None, start_index
            
        # 解析Begin Object行
        begin_line = lines[start_index].strip()
        
        # 提取Begin Object行的属性
        obj = {}
        begin_attrs = re.findall(r'(\w+)=([^\s]+)', begin_line)
        for key, value in begin_attrs:
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            obj[key] = value
        
        # 初始化Objects数组用于存放嵌套对象
        obj["Objects"] = []
        
        current_index = start_index + 1
        
        while current_index < len(lines):
            line = lines[current_index].strip()
            
            if not line:
                current_index += 1
                continue
                
            if line.startswith('Begin Object'):
                nested_obj, current_index = parse_object(lines, current_index)
                if nested_obj:
                    obj["Objects"].append(nested_obj)
                continue
                
            elif line == 'End Object':
                return obj, current_index + 1
                
            elif '=' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    
                    obj[key] = value
            
            current_index += 1
        
        return obj, current_index
    
    # 主解析逻辑
    lines = content.split('\n')
    root_objects = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('Begin Object'):
            obj, i = parse_object(lines, i)
            if obj:
                root_objects.append(obj)
        else:
            i += 1
    
    return root_objects[0] if root_objects else {}
    
def extract_widget_name(content_ref):
    """从Content引用中提取控件名称"""
    print(content_ref)
    # 例如：Button'\"WebViewTestUI:WidgetTree.CloseBtn\"' -> CloseBtn
    match = re.search(r'\"([^\"]+)\"', content_ref)
    if match:
        full_path = match.group(1)
        # 提取控件名称部分
        parts = full_path.split('.')
        return parts[-1] if parts else full_path
    return None
    
def parse_widget_blueprint(data):
    """合并WidgetTree节点并处理slot节点"""
    print("0:")
    print(data)
    # 获取两个WidgetTree节点
    widget_tree_1 = widget_tree_2 = None
    for obj in data.get('Objects', []):
        if obj.get('Name') != 'WidgetTree':
            continue
        if obj.get('Class') != None:
            widget_tree_1 = obj
        else:
            widget_tree_2 = obj
        if widget_tree_1 and widget_tree_2:
            break
    if not widget_tree_1 or not widget_tree_2:
        print("不包含多个WidgetTree")
        return data
    
    # 创建控件名称到对象的映射
    widget_map = {}
    
    # 处理第一个WidgetTree中的控件
    for widget in widget_tree_1.get('Objects', []):
        widget_name = widget.get('Name')
        if widget_name:
            widget_map[widget_name] = {
                'Class': widget.get('Class'),
                'Name': widget_name,
                'Objects': []  # 清空原有的Objects，我们将重新构建
            }
    print("1:")
    print(widget_map)
    
    # 处理第二个WidgetTree中的控件属性
    for widget in widget_tree_2.get('Objects', []):
        widget_name = widget.get('Name')
        if widget_name in widget_map:
            # 合并属性（排除Objects，因为我们要重新构建）
            for key, value in widget.items():
                if key not in ['Objects', 'Name']:
                    widget_map[widget_name][key] = value
    print("2:")
    print(widget_map)
    # 构建父子关系：处理slot节点
    print("2-1:")
    print(widget_tree_2)
    for widget in widget_tree_2.get('Objects', []):
        print("00000")
        widget_name = widget.get('Name')
        print("1111")
        # 检查是否有slot子节点
        if 'Objects' in widget and widget['Objects']:
            print("22222")
            for slot in widget['Objects']:
                print("33333")
                if 'Content' in slot:
                    print("44444")
                    content_ref = slot['Content']
                    child_name = extract_widget_name(content_ref)
                    
                    if child_name and child_name in widget_map:
                        # 将Content节点直接作为父节点的子节点
                        widget_map[widget_name]['Objects'].append(widget_map[child_name])
    print("3:")
    print(widget_map)
    # 构建根节点
    root_widget_ref = widget_tree_2.get('RootWidget', '')
    root_widget_name = extract_widget_name(root_widget_ref) if root_widget_ref else None
    print("4:")
    print(root_widget_name)
    # 创建新的WidgetTree结构
    new_widget_tree = {
        "Class": widget_tree_1["Class"],
        "Name": widget_tree_1["Name"],
        "Objects": []
    }
    
    # 添加根节点及其子节点
    if root_widget_name and root_widget_name in widget_map:
        new_widget_tree['Objects'].append(widget_map[root_widget_name])
    
    # 创建只包含WidgetTree的新数据结构
    result = {
        "WidgetTree": new_widget_tree
    }
    result = {}
    
    for k, v in data.items():
        if k != 'Objects':
            result[k] = v
        else:
            newv = []
            for obj in v:
                if obj['Name'] != 'WidgetTree':
                    newv.append(obj)
            newv.append({"WidgetTree": new_widget_tree})
            result[k] = newv
    
    return result

def convert_blueprint_to_json(input_file_path):
    """将Unreal Engine蓝图TXT文件转换为JSON文件"""
    if not os.path.exists(input_file_path):
        print(f"错误：文件 '{input_file_path}' 不存在")
        return
    
    file_dir = os.path.dirname(input_file_path)
    file_name = os.path.basename(input_file_path)
    file_name_without_ext = os.path.splitext(file_name)[0]
    output_file_path = os.path.join(file_dir, f"{file_name_without_ext}.json")
    
    print(f"正在解析文件: {input_file_path}")
    
    try:
        json_data = parse_ue_blueprint_file(input_file_path)
        
        objectclass = json_data["Class"]
        if objectclass == "/Script/UMGEditor.WidgetBlueprint":
            json_data = parse_widget_blueprint(json_data)
        
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=2)
        
        print(f"转换完成！JSON文件已保存为: {output_file_path}")
        
        def count_objects(obj):
            count = 1
            for nested in obj.get("Objects", []):
                count += count_objects(nested)
            return count
        
        if json_data:
            total_objects = count_objects(json_data)
            print(f"解析统计:")
            print(f"  - 主对象类: {json_data.get('Class', '未知')}")
            print(f"  - 主对象名称: {json_data.get('Name', '未命名')}")
            print(f"  - 总对象数量: {total_objects}")
            print(f"  - 嵌套层级: 包含 {len(json_data.get('Objects', []))} 个直接子对象")
        else:
            print("警告：未解析到任何对象")
            
    except Exception as e:
        print(f"解析过程中发生错误: {str(e)}")

# 使用示例
if __name__ == "__main__":
    # 如果提供了命令行参数，使用第一个参数作为文件路径
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        print("警告：没有输入文件")
        exit(-1)
    
    # 转换文件
    convert_blueprint_to_json(input_file)