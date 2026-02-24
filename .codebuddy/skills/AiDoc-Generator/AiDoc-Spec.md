# AiDoc 文档规范

**版本**: Current
**适用范围**: AiDoc 模块文档生成
**更新日期**: 2026-02-05

---

## 路径格式约束

### 模块文档路径约束
- `SOURCE_MAP.paths` 必须为**代码文件根目录相对路径**（相对于 `{CODE_ROOT}`，禁止绝对路径）
- `SOURCE_MAP.paths` 中的每个 `.cs` 必须真实存在；无法确认存在则不输出该条（必要时 StopExecution）
- **文档文件位置必须与源代码目录结构保持一致**：
  - 规则：去除源代码路径的 `{CODE_ROOT}` 前缀，替换为 `{AIDOC_ROOT}/`，`.cs` 改为 `.md`
  - 示例：`{CODE_ROOT}/GameBase/Event/BEventBus.cs` → `{AIDOC_ROOT}/GameBase/Event/BEventBus.md`
- 不得使用绝对路径
- 不得使用Token/Name代替路径
- 不得使用DocName代替路径

---

## 内容完整性约束

### 模块文档内容约束
- 每次生成模块文档前必须先完整阅读对应的源代码
- `KEYWORD_MAP.methods` **必须包含所有方法**，不得遗漏
- 方法名必须精确，不得使用模糊描述
- 不得包含实现细节（最小Token原则）
- 关键字必须覆盖所有方法的常用描述
- 一个关键字可以映射到多个方法名（用分号分隔或数组形式）

---

## 文档结构约束

### 模块文档结构
模块文档必须包含以下字段：

```yaml
KEYWORD_MAP:
  methods:
    "方法名": "关键词描述"

SOURCE_MAP:
  paths:
    - "相对路径/源代码文件.cs"
```

---

## 规范检查规则

### 模块文档规范检查
- 必须包含 `KEYWORD_MAP` 字段
- 不得包含源码级实现说明
- 路径必须使用相对路径（相对于 `{AIDOC_ROOT}`）
- `SOURCE_MAP.paths` 如果存在，必须使用相对路径（相对于 `{CODE_ROOT}`）
- 不得包含规范中未定义的自定义字段

---

## 文档模板

### 类文档模板

```yaml

# {ClassName}

KEYWORD_MAP:
  methods:
    "{MethodName1}": "关键词1;keyword1;关键词2;keyword2"
    "{MethodName2}": "关键词1;keyword1;关键词2;keyword2"
    "{MethodName3<T>}": "关键词1;keyword1;关键词2;keyword2"
    # 必须包含所有方法，不得遗漏

SOURCE_MAP:
  paths:
    - "{CodeRootRelativePath}.cs"
```

---

## 约束原则

### 零幻觉原则
生成的文档必须基于实际源代码结构，不得包含虚构内容

### 最小 Token 原则
文档只包含必要的字段和方法映射，不得包含冗余内容

### 最大约束原则
严格遵循 AiDoc 文档规范，不得添加未定义的字段

### 路径一致性原则
文档路径必须与源代码路径保持一致

### 相对路径原则
所有路径必须使用相对路径，不得使用绝对路径

### 完整性原则
`KEYWORD_MAP.methods` 必须包含所有方法，不得遗漏

### 准确性原则
方法名必须精确，不得使用模糊描述

### 先读后写原则
每次生成文档前必须先完整阅读对应的源代码