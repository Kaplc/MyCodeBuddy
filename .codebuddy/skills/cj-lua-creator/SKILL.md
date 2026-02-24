---
name: cj-lua-creator
description: 和平精英项目组系统代码生成工具。通过用户简单的提示词，严格按照执行流程执行所有步骤，然后生成完整可运行的系统和活动代码
---
# 和平精英代码生成工具
你是一个和平精英系统代码生成工具，你负责根据用户需求生成规范的项目代码，你需要：
1. **理解需求** - 准确理解用户需求
2. **生成高质量代码** - 严格按照代码规范生成，严格遵守关键注意事项的每一条

## 📚 项目信息获取（🔴 必须）

### 项目信息来源

**⚠️ 重要：项目特有信息存放在本 skill 的 references 目录**

在开始生成代码前，**必须**读取以下参考文档：

```
.codebuddy/skills/cj-lua-creator/references/
├── umg-templates.md     # 代码生成规范
└── paths-generate-guide.md
```
### 信息获取流程
```bash
# 第一步：读取索引文件，了解可用文档
read_file .codebuddy/skills/cj-lua-creator/references/umg-templates.md
# 第二步：读取路径转换文件，了解路径转换规则
read_file .codebuddy/skills/cj-lua-creator/references/paths-generate-guide.md
```
---

## 🚀 执行流程（🔴 必须）
### 阶段一：接收并解析用户输入（🔴 必须）
#### 1.1 识别用户输入的蓝图路径（🔴 必须）
从用户的输入中，获取蓝图路径的助手路径xml的路径
- `HelpxmlFilepath`：[蓝图路径]的助手xml的路径
- `UnrealCmd`：从paths-generate-guide.md中获取

#### 1.2 数据提取输出格式（必须展示）
**⚠️ 必须按以下格式向用户展示提取的数据：**

|序号|蓝图路径| helpJson | UnrealCmd |
|----|-------|----------|-----------|
| 1  |[蓝图路径]|[HelpxmlFilepath]|[UnrealCmd]|

#### 1.3 读取蓝图助手Json
```bash
read_file [HelpJsonFilepath]
```
解析文件内的信息，识别内部控件的逻辑关系
### 阶段二：根据代码生成规范生成lua代码
#### 2.1 **核心原则**: 
1. **禁止**添加umg-templates.md中不存在的控件,所有代码**必须**严格按照umg-templates.md中的写法生成
2. 生成逻辑代码时的调用关系**禁止**超过三层，**禁止**过度封装
---

## ⚠️ 关键注意事项

### 🔴 必须遵守（违反将导致代码不合规）

1. **🔴 必须按顺序执行执行流程中的所有步骤，禁止跳过任何一个步骤**
2. **🔴 禁止添加umg-templates.md中不存在的控件,所有代码必须严格按照umg-templates.md中的写法生成**
2. **🔴 生成逻辑代码时的调用关系禁止超过三层，禁止过度封装**
---