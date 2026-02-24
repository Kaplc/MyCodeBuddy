---
name: aidoc-indexer
description: Creates and updates AiDoc INDEX/README documents following AiDoc spec v2.1

# AiDoc-Indexer - AiDoc 索引文档生成

创建和更新 AiDoc 索引文档(INDEX.md / README.md),遵循 AiDoc 文档规范 v2.1。

**规范文档**: 参考 `SPEC.md` 获取详细的规范说明、约束条件和使用示例。

---

## Stage 0: 环境检测与初始化

**目标**: 自动检测项目的代码根目录和文档根目录

**执行时机**: 所有其他 Stage 之前

**伪代码流程**:

```
// ========== Stage 0: 环境检测与初始化 ==========

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

// 5. 扫描所有目录
所有目录列表 = []
FOR EACH dir IN 递归遍历({AIDOC_ROOT}/Doc) DO
    添加到 所有目录列表: dir绝对路径
END FOR

// 6. 扫描现有索引文件
现有索引文件列表 = []
FOR EACH file IN 递归遍历({AIDOC_ROOT}/Doc) DO
    IF file文件名 == "INDEX.md" OR file文件名 == "README.md" THEN
        添加到 现有索引文件列表:
            文件路径 = 相对路径(file, {AIDOC_ROOT}/Doc)
            绝对路径 = file
    END IF
END FOR

// 7. 计算统计结果
缺失索引目录列表 = []
多余索引文件列表 = []

// 检测缺失的索引文件
FOR EACH dir IN 所有目录列表 DO
    目录相对路径 = 相对路径(dir, {AIDOC_ROOT}/Doc)
    有索引文件 = False
    FOR EACH index IN 现有索引文件列表 DO
        IF index文件目录路径 == 目录相对路径 THEN
            有索引文件 = True
            跳出循环
        END IF
    END FOR
    IF 有索引文件 == False THEN
        添加到 缺失索引目录列表: 目录相对路径
    END IF
END FOR

// 检测多余的索引文件(索引文件存在但对应的目录不存在)
FOR EACH index IN 现有索引文件列表 DO
    索引目录 = index文件目录路径
    IF 索引目录 不在 所有目录列表 THEN
        添加到 多余索引文件列表: index文件路径
    END IF
END FOR

// 计算待创建、待更新、待删除的索引数量
待创建索引数量 = 缺失索引目录列表.length
待更新索引数量 = 0
FOR EACH index IN 现有索引文件列表 DO
    IF index文件目录路径 在 所有目录列表 THEN
        待更新索引数量 = 待更新索引数量 + 1
    END IF
END FOR
待删除索引数量 = 多余索引文件列表.length

// 8. 输出检测结果
输出分隔线和标题 "环境检测结果"
输出 "AiDoc/Doc 目录存在: " + AiDoc/Doc目录存在状态
输出 "AiDoc/Doc 路径: " + 实际路径
输出 "CODE_ROOT: " + {CODE_ROOT}
输出 "AIDOC_ROOT: " + {AIDOC_ROOT}
输出 "相对关系: " + 描述两个目录的关系
输出 "检测方式: " + 自动检测或用户指定

输出分隔线和标题 "文件扫描结果"
输出 "总目录数: " + 所有目录列表.length
输出 "现有索引: " + 现有索引文件列表.length
输出 "缺失索引: " + 缺失索引目录列表.length
输出 "多余索引: " + 多余索引文件列表.length
输出 "待创建索引: " + 待创建索引数量
输出 "待更新索引: " + 待更新索引数量
输出 "待删除索引: " + 待删除索引数量

// 9. 传递数据给后续 Stage
传递:
    - {CODE_ROOT}
    - {AIDOC_ROOT}
    - 所有目录列表
    - 现有索引文件列表
    - 缺失索引目录列表(待创建索引)
    - 多余索引文件列表(待删除索引)
```

**约束**: 参考 `SPEC.md` 中 "Stage 0 约束" 部分

---

## Stage 1: 创建索引文档

**目标**: 根据用户需求和 Stage 0 的检测结果,创建新的索引文档

**执行时机**: Stage 0 完成环境检测和文件扫描之后

**核心原则**:
- **创建索引文档**: 为指定目录创建新的索引文档(INDEX.md 或 README.md)
- **遵循规范**: 索引文档必须严格遵循 AiDoc 文档规范 v2.1 (详见 `SPEC.md`)
- **路径一致性**: 索引文档路径必须与源代码目录结构保持一致

**伪代码流程**:

```
// ========== Stage 1: 创建索引文档 ==========

// 第 1 步:构建创建索引文档的任务列表
从 Stage 0 获取 "缺失索引目录列表"
创建任务列表 = []

FOR i FROM 1 TO 缺失索引目录列表.length DO
    目录路径 = 缺失索引目录列表[i - 1]
    创建任务:
        type = "create"
        id = i
        priority = 1
        index_path = 目录路径 + "/" + 判断索引类型(目录路径)
        index_type = 判断索引类型(目录路径)  // INDEX.md 或 README.md
        status = "pending"
        dependencies = []
    添加到 创建任务列表
END FOR

输出创建任务列表:
    输出 "=== 创建索引文档任务列表 ==="
    输出 "ID | Type | Priority | Index Path | Index Type | Status | Dependencies"
    FOR EACH task IN 创建任务列表 DO
        输出 task.id + " | " + task.type + " | " + task.priority + " | " + task.index_path + " | " + task.index_type + " | " + task.status + " | []"
    END FOR
    输出 "- 总创建任务数: " + 创建任务列表.length

// 第 2 步:执行创建任务
FOR EACH create_task IN 创建任务列表 DO
    create_task.status = "in_progress"

    // 确定对应的源代码目录
    索引相对路径 = create_task.index_path
    源代码目录路径 = 索引路径转源代码路径(索引相对路径, {AIDOC_ROOT}, {CODE_ROOT})

    // 扫描源代码目录
    源代码文件列表 = []
    FOR EACH file IN 递归遍历(源代码目录路径) DO
        IF file扩展名 == ".cs" THEN
            添加到 源代码文件列表: file绝对路径
        END IF
    END FOR

    // 读取源代码内容
    源代码内容列表 = []
    FOR EACH file IN 源代码文件列表 DO
        源代码内容 = read_file_content(file)
        添加到 源代码内容列表:
            文件路径 = 相对路径(file, {CODE_ROOT})
            内容 = 源代码内容
            类名 = extract_class_name(源代码内容)
            命名空间 = extract_namespace(源代码内容)
            主要方法 = extract_main_methods(源代码内容)
    END FOR

    // 扫描子目录(用于生成索引路径)
    子目录列表 = []
    FOR EACH dir IN 直接子目录(源代码目录路径) DO
        子目录相对路径 = 相对路径(dir, {CODE_ROOT})
        添加到 子目录列表: 子目录相对路径
    END FOR

    // 扫描子模块文档(当前目录下的 .md 文件)
    子模块文档列表 = []
    文档目录路径 = 索引路径转文档路径(索引相对路径, {CODE_ROOT}, {AIDOC_ROOT})
    IF 文档目录路径 存在 THEN
        FOR EACH file IN 直接文件(文档目录路径) DO
            IF file扩展名 == ".md" AND file文件名 != "INDEX.md" AND file文件名 != "README.md" THEN
                添加到 子模块文档列表: 文件相对路径
            END IF
        END FOR
    END IF

    // 【重要】生成索引文档内容
    // 由大模型(AI)根据源代码内容生成索引文档
    // 索引文档结构参考 SPEC.md 中的 "索引文档模板"
    索引文档内容 = AI_生成_索引文档(
        源代码内容列表=源代码内容列表,
        子目录列表=子目录列表,
        子模块文档列表=子模块文档列表,
        索引类型=create_task.index_type,
        aidoc_root={AIDOC_ROOT}
    )

    // 创建索引文档
    索引绝对路径 = {AIDOC_ROOT} + "/Doc/" + create_task.index_path
    TRY
        write_file_content(索引绝对路径, 索引文档内容)
        create_task.status = "completed"
        创建结果 = "成功"
        错误信息 = ""
    CATCH 异常 e
        create_task.status = "failed"
        创建结果 = "失败"
        错误信息 = e.message
    END TRY

    // 输出单个任务执行结果
    输出 "[任务 " + create_task.id + "] " + create_task.index_path
    输出 "- 状态: " + 创建结果
    输出 "- 操作: 创建索引文档"
    IF 创建结果 == "成功" THEN
        输出 "- 结果: 文件已创建"
    ELSE
        输出 "- 错误: " + 错误信息
    END IF
END FOR

// 第 3 步:汇总创建结果
输出分隔线和标题 "索引文档创建报告"
成功数 = 0
失败数 = 0
FOR EACH task IN 创建任务列表 DO
    IF task.status == "completed" THEN
        成功数 = 成功数 + 1
    ELSE
        失败数 = 失败数 + 1
    END IF
END FOR

输出 "- 总创建任务数: " + 创建任务列表.length
输出 "- 成功: " + 成功数
输出 "- 失败: " + 失败数

输出分隔线和标题 "=== 创建任务列表 ==="
输出 "ID | Type | Priority | Index Path | Index Type | Status"
FOR EACH task IN 创建任务列表 DO
    输出 task.id + " | " + task.type + " | " + task.priority + " | " + task.index_path + " | " + task.index_type + " | " + task.status
END FOR

输出分隔线和标题 "=== 执行汇总 ==="
输出 "- 总操作数: " + 创建任务列表.length
输出 "- 成功: " + 成功数
输出 "- 失败: " + 失败数
```

**约束**: 参考 `SPEC.md` 中 "Stage 1 约束" 部分

---

## Stage 2: 更新索引文档

**目标**: 根据用户需求和 Stage 0 的检测结果,更新现有的索引文档

**执行时机**: Stage 1 完成索引文档创建之后

**核心原则**:
- **先检查后更新**: 使用Python扫描所有索引文件,检查是否符合规范,然后更新
- **更新索引文档**: 更新现有的索引文档内容,确保符合最新的源代码结构
- **遵循规范**: 索引文档必须严格遵循 AiDoc 文档规范 v2.1 (详见 `SPEC.md`)
- **保持一致性**: 更新后的索引文档必须与源代码目录结构保持一致

**伪代码流程**:

```
// ========== Stage 2: 更新索引文档 ==========

// 第 1 步:获取所有索引文件列表
所有索引文件列表 = 从 Stage 0 获取 "现有索引文件列表"

输出分隔线和标题 "=== 索引文件扫描结果 ==="
输出 "- 扫描索引文件总数: " + 所有索引文件列表.length

IF 所有索引文件列表.length > 0 THEN
    输出 "索引文件列表:"
    FOR i FROM 1 TO 所有索引文件列表.length DO
        输出 i + ". " + 所有索引文件列表[i - 1].文件路径
    END FOR
ELSE
    输出 "未找到任何索引文件"
END IF

// 第 2 步:由AI助手逐个检查索引文件规范
索引文件检查结果列表 = []

FOR EACH index_file IN 所有索引文件列表 DO
    索引绝对路径 = index_file.绝对路径
    索引内容 = read_file_content(索引绝对路径)

    // 人工审查索引内容是否符合规范
    // 规范检查规则参考 SPEC.md 中 "索引文档规范" 部分
    问题列表 = []

    IF 索引内容 不包含 "KEYWORD_MAP" 字段 THEN
        添加到 问题列表: "缺少KEYWORD_MAP字段"
    END IF

    IF 索引内容 包含 "MODULE_MAP" 字段 THEN
        添加到 问题列表: "包含MODULE_MAP字段(已废弃)"
    END IF

    IF 索引内容 包含源码级实现说明 THEN
        添加到 问题列表: "包含源码级实现说明"
    END IF

    IF 索引内容 使用绝对路径 THEN
        添加到 问题列表: "使用绝对路径"
    END IF

    IF 索引内容 包含未定义字段 THEN
        添加到 问题列表: "包含未定义的自定义字段"
    END IF

    // 判断是否符合规范
    IF 问题列表.length == 0 THEN
        符合规范状态 = "符合规范"
    ELSE
        符合规范状态 = "不符合规范"
    END IF

    添加到 索引文件检查结果列表:
        文件路径 = index_file.文件路径
        绝对路径 = 索引绝对路径
        符合规范 = 符合规范状态
        问题 = 问题列表
END FOR

// 输出规范检查结果
输出分隔线和标题 "=== 索引文档规范检查结果 ==="
输出 "文件总数: " + 所有索引文件列表.length
符合规范数 = 0
不符合规范数 = 0
FOR EACH result IN 索引文件检查结果列表 DO
    IF result.符合规范 == "符合规范" THEN
        符合规范数 = 符合规范数 + 1
    ELSE
        不符合规范数 = 不符合规范数 + 1
    END IF
END FOR
输出 "符合规范: " + 符合规范数
输出 "不符合规范: " + 不符合规范数

IF 不符合规范数 > 0 THEN
    输出 "不符合规范的索引列表:"
    FOR EACH result IN 索引文件检查结果列表 WHERE result.符合规范 == "不符合规范" DO
        输出 "1. " + result.文件路径
        FOR EACH problem IN result.问题 DO
            输出 "   - 问题: " + problem
        END FOR
    END FOR
END IF

// 第 3 步:构建更新索引文档的任务列表
更新任务列表 = []
FOR i FROM 1 TO 所有索引文件列表.length DO
    index_file = 所有索引文件列表[i - 1]
    问题列表 = []
    FOR EACH result IN 索引文件检查结果列表 DO
        IF result.文件路径 == index_file.文件路径 THEN
            问题列表 = result.问题
            跳出循环
        END IF
    END FOR

    创建任务:
        type = "update"
        id = i
        priority = 2
        index_path = index_file.文件路径
        index_type = 判断索引类型(index_file.文件路径)
        status = "pending"
        dependencies = []
        issues = 问题列表
    添加到 更新任务列表
END FOR

输出分隔线和标题 "=== 更新索引文档任务列表 ==="
输出 "ID | Type | Priority | Index Path | Index Type | Status | Dependencies | Issues"
FOR EACH task IN 更新任务列表 DO
    输出 task.id + " | " + task.type + " | " + task.priority + " | " + task.index_path + " | " + task.index_type + " | " + task.status + " | [] | " + task.issues.join("; ")
END FOR
输出 "- 总更新任务数: " + 更新任务列表.length

// 第 4 步:执行更新任务
FOR EACH update_task IN 更新任务列表 DO
    update_task.status = "in_progress"

    // 确定对应的源代码目录
    索引相对路径 = update_task.index_path
    源代码目录路径 = 索引路径转源代码路径(索引相对路径, {AIDOC_ROOT}, {CODE_ROOT})

    // 扫描源代码目录
    源代码文件列表 = []
    FOR EACH file IN 递归遍历(源代码目录路径) DO
        IF file扩展名 == ".cs" THEN
            添加到 源代码文件列表: file绝对路径
        END IF
    END FOR

    // 读取源代码内容
    源代码内容列表 = []
    FOR EACH file IN 源代码文件列表 DO
        源代码内容 = read_file_content(file)
        添加到 源代码内容列表:
            文件路径 = 相对路径(file, {CODE_ROOT})
            内容 = 源代码内容
            类名 = extract_class_name(源代码内容)
            命名空间 = extract_namespace(源代码内容)
            主要方法 = extract_main_methods(源代码内容)
    END FOR

    // 扫描子目录(用于生成索引路径)
    子目录列表 = []
    FOR EACH dir IN 直接子目录(源代码目录路径) DO
        子目录相对路径 = 相对路径(dir, {CODE_ROOT})
        添加到 子目录列表: 子目录相对路径
    END FOR

    // 扫描子模块文档(当前目录下的 .md 文件)
    子模块文档列表 = []
    文档目录路径 = 索引路径转文档路径(索引相对路径, {CODE_ROOT}, {AIDOC_ROOT})
    IF 文档目录路径 存在 THEN
        FOR EACH file IN 直接文件(文档目录路径) DO
            IF file扩展名 == ".md" AND file文件名 != "INDEX.md" AND file文件名 != "README.md" THEN
                添加到 子模块文档列表: 文件相对路径
            END IF
        END FOR
    END IF

    // 读取现有索引文档内容
    索引绝对路径 = {AIDOC_ROOT} + "/Doc/" + update_task.index_path
    现有索引内容 = read_file_content(索引绝对路径)

    // 【重要】生成更新后的索引文档内容
    // 由大模型(AI)根据源代码、现有索引和规范文档直接生成
    // 索引文档结构参考 SPEC.md 中的 "索引文档模板"
    // 根据任务的问题列表修复规范问题
    更新后的索引内容 = AI_生成_更新索引文档(
        源代码内容列表=源代码内容列表,
        子目录列表=子目录列表,
        子模块文档列表=子模块文档列表,
        现有索引内容=现有索引内容,
        问题列表=update_task.issues,
        aidoc_root={AIDOC_ROOT}
    )

    // 写入更新后的文档
    TRY
        write_file_content(索引绝对路径, 更新后的索引内容)
        update_task.status = "completed"
        更新结果 = "成功"
        错误信息 = ""
    CATCH 异常 e
        update_task.status = "failed"
        更新结果 = "失败"
        错误信息 = e.message
    END TRY

    // 输出单个任务执行结果
    输出 "[任务 " + update_task.id + "] " + update_task.index_path
    输出 "- 状态: " + 更新结果
    输出 "- 操作: 更新索引文档"
    IF 更新结果 == "成功" THEN
        输出 "- 结果: 文件已更新"
    ELSE
        输出 "- 错误: " + 错误信息
    END IF
END FOR

// 第 5 步:汇总更新结果
输出分隔线和标题 "索引文档更新报告"
成功数 = 0
失败数 = 0
FOR EACH task IN 更新任务列表 DO
    IF task.status == "completed" THEN
        成功数 = 成功数 + 1
    ELSE
        失败数 = 失败数 + 1
    END IF
END FOR

输出 "- 总更新任务数: " + 更新任务列表.length
输出 "- 成功: " + 成功数
输出 "- 失败: " + 失败数

输出分隔线和标题 "=== 规范检查结果 ==="
输出 "- 审查索引文件总数: " + 所有索引文件列表.length
输出 "- 符合规范的索引: " + 符合规范数
输出 "- 不符合规范的索引: " + 不符合规范数

输出分隔线和标题 "=== 更新任务列表 ==="
输出 "ID | Type | Priority | Index Path | Index Type | Issues | Status"
FOR EACH task IN 更新任务列表 DO
    输出 task.id + " | " + task.type + " | " + task.priority + " | " + task.index_path + " | " + task.index_type + " | " + task.issues.join("; ") + " | " + task.status
END FOR

输出分隔线和标题 "=== 执行汇总 ==="
输出 "- 总操作数: " + 更新任务列表.length
输出 "- 成功: " + 成功数
输出 "- 失败: " + 失败数
```

**约束**: 参考 `SPEC.md` 中 "Stage 2 约束" 部分

---

## Stage 3: 修复不符合规范的索引文档

**目标**: 由AI助手逐个审查所有索引文档,识别不符合规范的内容并进行修复(可选步骤)

**执行时机**: Stage 2 完成索引文档更新之后(可选,用于补充验证)

**核心原则**:
- **可选步骤**: 此步骤为可选步骤,如果Stage 2已通过Python扫描完成了规范检查和修复,则此步骤可跳过
- **逐个审查**: 由AI助手逐个读取索引文件,人工判断是否符合规范
- **修复不符合规范的索引**: 删除不符合规范的内容,补充缺失的必要字段
- **保留规范要求的内容**: 不得删除规范要求保留的字段

**伪代码流程**:

```
// ========== Stage 3: 修复不符合规范的索引文档 ==========

// 【注意】此为可选步骤,如果 Stage 2 已通过规范检查和修复,则可跳过

// 第 1 步:逐个审查索引文档
所有索引文件列表 = 从 Stage 0 获取 "现有索引文件列表"

索引文件审查结果列表 = []

FOR EACH index_file IN 所有索引文件列表 DO
    索引绝对路径 = index_file.绝对路径
    索引内容 = read_file_content(索引绝对路径)

    // 人工审查索引内容是否符合规范
    // 规范检查规则参考 SPEC.md 中 "索引文档规范" 部分
    问题列表 = []

    IF 索引内容 不包含 "KEYWORD_MAP" 字段 THEN
        添加到 问题列表: "缺少KEYWORD_MAP字段"
    END IF

    IF 索引内容 包含 "MODULE_MAP" 字段 THEN
        添加到 问题列表: "包含MODULE_MAP字段(已废弃)"
    END IF

    IF 索引内容 包含源码级实现说明 THEN
        添加到 问题列表: "包含源码级实现说明"
    END IF

    IF 索引内容 使用绝对路径 THEN
        添加到 问题列表: "使用绝对路径"
    END IF

    IF 索引内容 包含未定义字段 THEN
        添加到 问题列表: "包含未定义的自定义字段"
    END IF

    // 判断是否符合规范
    IF 问题列表.length == 0 THEN
        符合规范状态 = "符合规范"
        需要修复 = False
    ELSE
        符合规范状态 = "不符合规范"
        需要修复 = True
    END IF

    添加到 索引文件审查结果列表:
        文件路径 = index_file.文件路径
        绝对路径 = 索引绝对路径
        符合规范 = 符合规范状态
        问题 = 问题列表
        需要修复 = 需要修复
END FOR

// 输出审查结果
输出分隔线和标题 "=== 索引文档审查结果 ==="
输出 "文件总数: " + 所有索引文件列表.length
符合规范数 = 0
不符合规范数 = 0
FOR EACH result IN 索引文件审查结果列表 DO
    IF result.符合规范 == "符合规范" THEN
        符合规范数 = 符合规范数 + 1
    ELSE
        不符合规范数 = 不符合规范数 + 1
    END IF
END FOR
输出 "符合规范: " + 符合规范数
输出 "不符合规范: " + 不符合规范数

IF 不符合规范数 > 0 THEN
    输出 "不符合规范的索引列表:"
    FOR EACH result IN 索引文件审查结果列表 WHERE result.符合规范 == "不符合规范" DO
        输出 "1. " + result.文件路径
        FOR EACH problem IN result.问题 DO
            输出 "   - 问题: " + problem
        END FOR
    END FOR
END IF

// 第 2 步:构建修复不符合规范索引文档的任务列表
修复任务列表 = []
任务ID = 1

FOR EACH result IN 索引文件审查结果列表 DO
    IF result.需要修复 THEN
        创建任务:
            type = "repair"
            id = 任务ID
            priority = 3
            index_path = result.文件路径
            index_type = 判断索引类型(result.文件路径)
            status = "pending"
            dependencies = []
            issues = result.问题
        添加到 修复任务列表
        任务ID = 任务ID + 1
    END IF
END FOR

IF 修复任务列表.length > 0 THEN
    输出分隔线和标题 "=== 修复不符合规范索引文档任务列表 ==="
    输出 "ID | Type | Priority | Index Path | Issues | Status | Dependencies"
    FOR EACH task IN 修复任务列表 DO
        输出 task.id + " | " + task.type + " | " + task.priority + " | " + task.index_path + " | " + task.issues.join("; ") + " | " + task.status + " | []"
    END FOR
    输出 "- 总修复任务数: " + 修复任务列表.length
ELSE
    输出 "无需修复任务,所有索引文档均符合规范"
    跳过此 Stage
END IF

// 第 3 步:执行修复任务
FOR EACH repair_task IN 修复任务列表 DO
    repair_task.status = "in_progress"

    // 确定对应的源代码目录
    索引相对路径 = repair_task.index_path
    源代码目录路径 = 索引路径转源代码路径(索引相对路径, {AIDOC_ROOT}, {CODE_ROOT})

    // 扫描源代码目录
    源代码文件列表 = []
    FOR EACH file IN 递归遍历(源代码目录路径) DO
        IF file扩展名 == ".cs" THEN
            添加到 源代码文件列表: file绝对路径
        END IF
    END FOR

    // 读取源代码内容
    源代码内容列表 = []
    FOR EACH file IN 源代码文件列表 DO
        源代码内容 = read_file_content(file)
        添加到 源代码内容列表:
            文件路径 = 相对路径(file, {CODE_ROOT})
            内容 = 源代码内容
            类名 = extract_class_name(源代码内容)
            命名空间 = extract_namespace(源代码内容)
            主要方法 = extract_main_methods(源代码内容)
    END FOR

    // 读取索引文档内容
    索引绝对路径 = {AIDOC_ROOT} + "/Doc/" + repair_task.index_path
    现有索引内容 = read_file_content(索引绝对路径)

    // 【重要】生成修复后的索引文档内容
    // 由大模型(AI)根据源代码、现有索引和问题列表直接生成
    // 索引文档结构参考 SPEC.md 中的 "索引文档模板"
    修复后的索引内容 = AI_修复_索引文档(
        源代码内容列表=源代码内容列表,
        现有索引内容=现有索引内容,
        问题列表=repair_task.issues,
        aidoc_root={AIDOC_ROOT}
    )

    // 写入修复后的文档
    TRY
        write_file_content(索引绝对路径, 修复后的索引内容)
        repair_task.status = "completed"
        修复结果 = "成功"
        错误信息 = ""
    CATCH 异常 e
        repair_task.status = "failed"
        修复结果 = "失败"
        错误信息 = e.message
    END TRY

    // 输出单个任务执行结果
    输出 "[任务 " + repair_task.id + "] " + repair_task.index_path
    输出 "- 状态: " + 修复结果
    输出 "- 操作: 修复索引文档"
    IF 修复结果 == "成功" THEN
        输出 "- 结果: 文件已修复"
    ELSE
        输出 "- 错误: " + 错误信息
    END IF
END FOR

// 第 4 步:汇总修复结果
输出分隔线和标题 "索引文档修复报告"
成功数 = 0
失败数 = 0
FOR EACH task IN 修复任务列表 DO
    IF task.status == "completed" THEN
        成功数 = 成功数 + 1
    ELSE
        失败数 = 失败数 + 1
    END IF
END FOR

输出 "- 总修复任务数: " + 修复任务列表.length
输出 "- 成功: " + 成功数
输出 "- 失败: " + 失败数

输出分隔线和标题 "=== 审查结果汇总 ==="
输出 "- 审查索引文件总数: " + 所有索引文件列表.length
输出 "- 符合规范的索引: " + 符合规范数
输出 "- 不符合规范的索引: " + 不符合规范数

输出分隔线和标题 "=== 修复任务列表 ==="
输出 "ID | Type | Priority | Index Path | Issues | Status"
FOR EACH task IN 修复任务列表 DO
    输出 task.id + " | " + task.type + " | " + task.priority + " | " + task.index_path + " | " + task.issues.join("; ") + " | " + task.status
END FOR

输出分隔线和标题 "=== 执行汇总 ==="
输出 "- 总操作数: " + 修复任务列表.length
输出 "- 成功: " + 成功数
输出 "- 失败: " + 失败数
```

**约束**: 参考 `SPEC.md` 中 "Stage 3 约束" 部分
