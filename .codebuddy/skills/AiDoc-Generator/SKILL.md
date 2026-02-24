---
name: aidoc-module-generator
description: Generates and updates AiDoc module .md documents for classes/components following AiDoc spec. Invoke when user asks to create or update module documentation.
---

# AiDoc-Module-Generator - AiDoc 模块文档生成

**核心目标**: 专门用于创建和更新 AiDoc 模块文档（类/组件文档），严格遵循 AiDoc 文档规范，确保零幻觉、最小 token、最大约束。

**重要说明**:
- **文档内容生成**：由大模型（AI）根据源代码和规范文档直接生成
- **纯伪代码执行**：所有流程以伪代码形式描述，无需外部工具支持

---
## Stage 0: 环境检测与初始化（Environment Detection & Initialization）

**目标**: 自动检测项目的代码根目录和文档根目录，为后续流程提供基础路径信息

**执行时机**: 所有其他 Stage 之前，必须首先执行

**伪代码流程**:

```
// ========== Stage 0: 环境检测与初始化 ==========

// 0. 加载文档规范
加载 AiDoc-Spec.md 获取 path_constraints, content_constraints, check_rules

// 1. 查询 AiDoc/Doc 目录是否存在
IF AiDoc/Doc 目录存在 THEN
    记录 AiDoc/Doc 路径
ELSE
    询问用户要在哪里创建 AiDoc/Doc 目录
    等待用户选择创建位置
    创建 AiDoc/Doc 目录
END IF

// 2. 检测代码根目录 {CODE_ROOT}
{CODE_ROOT} = 自动检测_代码根目录()
    优先级: .sln文件 > .csproj文件 > Assets/Scripts或Source或src的父目录
IF 无法自动检测 THEN
    要求用户明确指定代码根目录
END IF

// 3. 检测文档根目录 {AIDOC_ROOT}
IF AiDoc/Doc 目录已存在 THEN
    {AIDOC_ROOT} = AiDoc 目录路径 (AiDoc/Doc的父目录)
ELSE
    根据用户选择的位置创建 AiDoc/Doc 目录
    {AIDOC_ROOT} = 创建的 AiDoc 目录路径
END IF

// 4. 验证路径关系
记录 {AIDOC_ROOT} 和 {CODE_ROOT} 的相对关系

// 5. 扫描缺失的模块文档
// 扫描源代码文件和现有文档，生成待创建和待更新的文档列表
待创建模块文档列表 = []
待更新模块文档列表 = []

// 如果用户指定了源代码路径
IF 用户指定了 source_paths THEN
    FOR EACH source_path IN source_paths DO
        source_file_path = {CODE_ROOT} + "/" + source_path
        IF source_file_path 存在 THEN
            // 计算对应的文档路径
            doc_path = 源代码路径转文档路径(source_path, {CODE_ROOT}, {AIDOC_ROOT})
            doc_abs_path = {AIDOC_ROOT} + "/Doc/" + doc_path
            IF doc_abs_path 存在 THEN
                添加到 待更新模块文档列表:
                    module_doc_path = doc_path
                    source_path = source_path
                    doc_absolute_path = doc_abs_path
            ELSE
                添加到 待创建模块文档列表:
                    module_doc_path = doc_path
                    source_path = source_path
            END IF
        END IF
    END FOR
END IF

// 如果用户指定了类名
IF 用户指定了 class_names THEN
    FOR EACH class_name IN class_names DO
        // 在代码库中搜索该类
        source_abs_path = 在代码库中搜索类文件(class_name, {CODE_ROOT})
        IF 找到源文件 THEN
            source_path = 源文件相对路径(source_abs_path, {CODE_ROOT})
            doc_path = 源代码路径转文档路径(source_path, {CODE_ROOT}, {AIDOC_ROOT})
            doc_abs_path = {AIDOC_ROOT} + "/Doc/" + doc_path
            IF doc_abs_path 存在 THEN
                添加到 待更新模块文档列表:
                    module_doc_path = doc_path
                    source_path = source_path
                    doc_absolute_path = doc_abs_path
            ELSE
                添加到 待创建模块文档列表:
                    module_doc_path = doc_path
                    source_path = source_path
            END IF
        END IF
    END FOR
END IF

// 如果用户指定了现有文档路径
IF 用户指定了 doc_paths THEN
    FOR EACH doc_path IN doc_paths DO
        doc_abs_path = {AIDOC_ROOT} + "/Doc/" + doc_path
        IF doc_abs_path 存在 THEN
            // 从文档中读取源代码路径
            existing_doc = read_file_content(doc_abs_path)
            source_path = 从文档中提取源代码路径(existing_doc, {CODE_ROOT})
            IF source_path 存在 THEN
                添加到 待更新模块文档列表:
                    module_doc_path = doc_path
                    source_path = source_path
                    doc_absolute_path = doc_abs_path
            END IF
        END IF
    END FOR
END IF

// 生成扫描结果清单
输出 "待创建模块文档: " + 待创建模块文档列表.length + " 个"
输出 "待更新模块文档: " + 待更新模块文档列表.length + " 个"

// 6. 输出检测结果
输出环境检测结果
输出缺失模块文档扫描结果

// 传递数据给 Stage 1
传递:
    - {CODE_ROOT}
    - {AIDOC_ROOT}
    - 待创建模块文档列表
    - 待更新模块文档列表（仅用户指定的）
```

---

## Stage 1: 创建模块文档（Create Module Documents）

**目标**: 根据用户需求和 Stage 0 的检测结果，为指定的类/组件创建新的模块文档

**执行时机**: Stage 0 完成环境检测和文件扫描之后

**伪代码流程**:

```
// ========== Stage 1: 创建模块文档 ==========

// 第 1 步：构建创建任务列表
从 Stage 0 获取"待创建模块文档"列表

FOR EACH 待创建模块文档 DO
    创建任务:
        type = "create"
        priority = 1
        module_doc_path = 模块文档相对路径
        source_path = 对应的源代码文件相对路径
        status = "pending"
        dependencies = []
END FOR

输出创建任务列表

// 第 2 步：执行创建任务
FOR EACH create_task IN create_list DO
    task.status = "in_progress"
    
    // 读取源代码
    source_abs_path = {CODE_ROOT} + "/" + create_task.source_path
    source_code = read_file_content(source_abs_path)
    
    // 提取信息（仅用于辅助理解）
    class_name = extract_class_name(source_code)
    methods = extract_methods(source_code)
    
    // 【重要】文档内容由大模型（AI）直接生成
    doc_content = AI_生成_完整文档(source_code, {CODE_ROOT}, {AIDOC_ROOT})
    
    // 写入文档
    doc_abs_path = {AIDOC_ROOT} + "/Doc/" + create_task.module_doc_path
    write_file_content(doc_abs_path, doc_content)
    
    task.status = "completed"
END FOR

// 第 3 步：汇总创建结果
输出模块文档创建报告:
    - 总创建任务数
    - 成功数
    - 失败数
    - 每个任务的执行详情
```

**注意**:
- `doc_content` 必须由大模型（AI）根据源代码和规范文档直接生成
- 伪代码描述了文件读取和写入的操作流程

---

## Stage 2: 更新模块文档（Update Module Documents）

**目标**: 根据用户需求和 Stage 0 的检测结果，更新现有的模块文档

**执行时机**: Stage 1 完成模块文档创建之后

**伪代码流程**:

```
// ========== Stage 2: 更新模块文档 ==========

// 第 1 步：构建更新任务列表
从 Stage 0 获取"待更新模块文档"列表

FOR EACH 待更新模块文档 DO
    创建任务:
        type = "update"
        priority = 2
        module_doc_path = 模块文档相对路径
        source_path = 对应的源代码文件相对路径
        status = "pending"
        dependencies = []
END FOR

输出更新任务列表

// 第 2 步：收集所有待更新文件内容
待更新文件内容列表 = []

FOR EACH update_task IN update_list DO
    // 读取源代码内容
    source_abs_path = {CODE_ROOT} + "/" + update_task.source_path
    source_code = read_file_content(source_abs_path)

    // 读取现有文档内容
    doc_abs_path = update_task.doc_absolute_path
    existing_doc = read_file_content(doc_abs_path)

    // 添加到文件内容列表
    添加到 待更新文件内容列表:
        module_doc_path = update_task.module_doc_path
        source_path = update_task.source_path
        doc_absolute_path = update_task.doc_absolute_path
        source_content = source_code
        doc_content = existing_doc
END FOR

输出 "已收集 " + 待更新文件内容列表.length + " 个待更新文件内容"

// 第 3 步：大模型读取文件并加载文档规范进行判断
FOR EACH file_info IN 待更新文件内容列表 DO
    // 加载 AiDoc 文档规范
    加载 AiDoc-Spec.md 文档规范内容

    // 读取源代码内容
    source_code = file_info['source_content']

    // 读取现有文档内容
    existing_doc = file_info['doc_content']

    // 【重要规范验证原则】大模型对比文档规范时：
    // - 不需要考虑内容的顺序来确定是否符合
    // - 只关注内容是否完整（不缺少必要的字段和方法）
    // - 只要文档包含所有必需的字段（KEYWORD_MAP、SOURCE_MAP等）和方法映射，即认为符合规范
    // - 字段内元素的顺序不影响规范符合性判断

    // 大模型分析并判断:
    // 1. 分析源代码的变更（新增方法、删除方法、修改方法等）
    // 2. 对比现有文档的内容和结构（不关注顺序，只关注完整性）
    // 3. 检查现有文档是否符合 AiDoc 文档规范（内容完整即符合）
    // 4. 生成更新后的文档内容

    // 【重要】文档内容由大模型（AI）根据源代码、现有文档和规范文档直接生成
    // 包括更新的 YAML 头部、功能说明，保留有效的非YAML内容
    updated_doc = AI_生成_更新文档(
        source_code=source_code,
        existing_doc=existing_doc,
        code_root={CODE_ROOT},
        aidoc_root={AIDOC_ROOT},
        aidoc_spec=AiDoc_Spec_内容
    )

    // 写入更新后的文档
    doc_abs_path = file_info['doc_absolute_path']
    write_file_content(doc_abs_path, updated_doc)
END FOR

// 第 3 步：汇总更新结果
输出模块文档更新报告:
    - 总更新任务数
    - 成功数
    - 失败数
    - 每个任务的执行详情
```

**注意**:
- `updated_doc` 必须由大模型（AI）根据源代码和规范文档直接生成
- 伪代码描述了文件读取、写入和解析的操作流程

---

## 使用示例（Usage Examples）

> **模板位置**: [AiDoc-Spec.md](./AiDoc-Spec.md) - 文档模板章节
> **加载方式**: 按需从规范文件加载模板内容

**伪代码流程**:

```
// ========== 文档模板加载 ==========

// 加载规范文件
utils = create_aidoc_utils("./AiDoc-Spec.md")
spec = utils.load_aidoc_spec()

// 加载文档模板
template_manager = create_template_manager(utils)
templates = template_manager.load_document_templates()

// 根据文档类型获取模板
class_template = template_manager.get_template_by_type('class')
component_template = template_manager.get_template_by_type('component')
index_template = template_manager.get_template_by_type('index')
readme_template = template_manager.get_template_by_type('readme')

// 自动检测文档类型
doc_type = template_manager.determine_document_type(source_code)
template = template_manager.get_template_by_type(doc_type)
```

**可用模板类型**:
- **类文档模板**: 用于生成类的模块文档
- **组件文档模板**: 用于生成组件的模块文档  
- **索引文档模板（README.md）**: 用于生成目录索引文档
- **索引文档模板（INDEX.md）**: 用于生成根目录索引文档

> 详细模板内容和格式请参考 [AiDoc-Spec.md](./AiDoc-Spec.md) 文件的"文档模板"章节

---

## 使用示例（Usage Examples）

### 示例 1: 为单个类创建模块文档

**用户输入**:
```
为 BEventBus 类创建模块文档
```

**执行流程**:
1. Stage 0: 检测环境，扫描 BEventBus.cs 文件
2. Stage 1: 创建 GameBase/Event/BEventBus.md
3. 输出创建结果

### 示例 2: 更新所有模块文档

**用户输入**:
```
更新所有模块文档
```

**执行流程**:
1. Stage 0: 检测环境，扫描所有模块文档
2. Stage 1: 创建缺失的模块文档
3. Stage 2: 更新现有的模块文档
4. Stage 3: 修复不符合规范的模块文档
5. 输出完整报告

### 示例 3: 为指定路径的类创建模块文档

**用户输入**:
```
为 GameBase/Utility/Helper.cs 创建模块文档
```

**执行流程**:
1. Stage 0: 检测环境，扫描指定源代码文件
2. Stage 1: 创建 GameBase/Utility/Helper.md
3. 输出创建结果

---

## 注意事项（Important Notes）

> **约束原则**: [AiDoc-Spec.md](./AiDoc-Spec.md) - 约束原则章节
> **加载方式**: 执行时自动加载并应用所有约束原则

**伪代码流程**:

```
// ========== 约束原则应用 ==========

// 加载规范文件
utils = create_aidoc_utils("./AiDoc-Spec.md")
spec = utils.load_aidoc_spec()

// 应用AiDoc文档约束原则
constraint_manager = create_constraint_manager(utils)
constraints = constraint_manager.apply_aidoc_constraints()

// 验证文档符合性
// 【重要规范验证原则】验证时关注内容完整性而非顺序：
// - 不要求字段或元素的顺序与规范完全一致
// - 只要包含所有必需的字段和方法映射即符合规范
// - YAML 字段内的元素顺序不影响符合性判断
validation_result = constraint_manager.validate_document_compliance(doc_content, 'module')

IF validation_result['is_compliant'] THEN
    输出 "文档符合规范"
ELSE
    输出 "文档不符合规范，问题: " + validation_result['issues']
END IF
```

**核心约束原则**:
- **zero_hallucination**: 零幻觉原则
- **minimal_token**: 最小Token原则  
- **maximum_constraint**: 最大约束原则
- **path_consistency**: 路径一致性原则
- **relative_path**: 相对路径原则
- **completeness**: 完整性原则
- **accuracy**: 准确性原则
- **read_before_write**: 先读后写原则

**关键执行要求**:
1. **规范遵循**: 严格遵循 [AiDoc-Spec.md](./AiDoc-Spec.md) 中定义的所有约束
2. **按需加载**: 执行时自动加载规范文件，确保使用最新规范
3. **零幻觉**: 生成内容必须基于实际源代码，不得虚构
4. **路径一致**: 文档路径与源代码路径保持严格一致
5. **完整覆盖**: 方法映射必须包含所有方法，不得遗漏
6. **先读后写**: 生成前必须完整读取源代码内容

> 详细约束原则和执行规范请参考 [AiDoc-Spec.md](./AiDoc-Spec.md) 文件