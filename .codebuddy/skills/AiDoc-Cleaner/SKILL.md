---
name: aidoc-cleaner
description: 清理 AiDoc 文档目录，删除多余文档、空目录和非 Markdown 文件，确保文档目录结构与源代码目录结构一致。专门用于文档清理，严格遵循 AiDoc 文档规范。
---

# AiDoc-Cleaner - AiDoc 文档清理

**核心目标**: 扫描 AiDoc 文档目录，检测多余文档、空目录和非 Markdown 文件，按文件扩展名分类展示，让用户选择性地清理，确保文档目录结构与源代码目录结构一致。

**重要说明**:
- **扫描与清理**：由大模型（AI）根据源代码目录和文档目录直接分析
- **纯伪代码执行**：所有流程以伪代码形式描述，无需外部工具支持

---

## Stage 0: 环境检测与扫描（Environment Detection & Scanning）

**目标**: 自动检测项目的代码根目录和文档根目录，扫描所有需要清理的文件和目录，按扩展名分类统计

**执行时机**: 所有其他 Stage 之前，必须首先执行

**伪代码流程**:

```
// ========== Stage 0: 环境检测与扫描 ==========

// 1. 检测代码根目录 {CODE_ROOT}
{CODE_ROOT} = 自动检测_代码根目录()
    优先级: .sln文件 > .csproj文件 > Assets/Scripts或Source或src的父目录
IF 无法自动检测 THEN
    要求用户明确指定代码根目录
END IF

// 2. 检测文档根目录 {AIDOC_ROOT}
{AIDOC_ROOT} = {CODE_ROOT} + "/Assets/Scripts/AiDoc/Doc"
IF {AIDOC_ROOT} 目录不存在 THEN
    输出错误并停止执行
END IF

// 3. 扫描源代码文件
源代码文件列表 = []
FOR EACH file IN 递归遍历({CODE_ROOT}) DO
    IF file 不是 AiDoc目录 AND file扩展名 == ".cs" THEN
        添加到 源代码文件列表:
            文件路径 = 相对路径(file, {CODE_ROOT})
            绝对路径 = file
    END IF
END FOR

// 4. 扫描文档文件
文档文件列表 = []
FOR EACH file IN 递归遍历({AIDOC_ROOT}) DO
    IF file扩展名 == ".md" THEN
        添加到 文档文件列表:
            文件路径 = 相对路径(file, {AIDOC_ROOT})
            绝对路径 = file
    END IF
END FOR

// 5. 扫描所有文件并按扩展名分组（排除 Markdown 文件的 meta 文件）
非Markdown文件列表 = []
扩展名分组 = {}
meta扩展名排除列表 = [".meta"]

FOR EACH file IN 递归遍历({AIDOC_ROOT}) DO
    IF file扩展名 != ".md" AND file扩展名 != "" THEN
        // 检查是否为 Markdown 文件的 meta 文件
        IF file扩展名 IN meta扩展名排除列表 THEN
            文件基础名 = 去除扩展名(获取文件名(file))
            IF 文件基础名.endsWith(".md") THEN
                // 这是 Markdown 文件的 meta 文件，跳过
                CONTINUE
            END IF
        END IF

        添加到 非Markdown文件列表:
            文件路径 = 相对路径(file, {AIDOC_ROOT})
            绝对路径 = file
            扩展名 = file扩展名

        // 按扩展名分组
        IF 扩展名分组[file扩展名] 不存在 THEN
            扩展名分组[file扩展名] = []
        END IF
        添加到 扩展名分组[file扩展名]
    END IF
END FOR

// 6. 扫描空目录
空目录列表 = []
FOR EACH dir IN 自底向上遍历({AIDOC_ROOT}) DO
    IF 目录为空(dir) THEN
        添加到 空目录列表:
            目录路径 = 相对路径(dir, {AIDOC_ROOT})
            绝对路径 = dir
    END IF
END FOR

// 7. 对比目录结构，查找多余文档
索引文件集合 = ["README.md", "INDEX.md", "SUMMARY.md", "GUIDE.md"]
多余文档列表 = []
FOR EACH doc IN 文档文件列表 DO
    IF doc文件名 不在 索引文件集合 THEN
        源代码路径 = 将doc路径中的.md替换为.cs
        源代码绝对路径 = {CODE_ROOT} + "/" + 源代码路径
        IF 源代码绝对路径 不存在 THEN
            添加到 多余文档列表:
                文档路径 = doc文件路径
                绝对路径 = doc绝对路径
        END IF
    END IF
END FOR

// 8. 统计非 Markdown 文件总数
非Markdown文件总数 = 非Markdown文件列表.length

// 9. 输出检测结果
输出分隔线和标题
输出 "代码根目录: " + {CODE_ROOT}
输出 "文档根目录: " + {AIDOC_ROOT}
输出 "源代码文件数: " + 源代码文件列表.length
输出 "文档文件数: " + 文档文件列表.length
输出 "多余文档数: " + 多余文档列表.length
输出 "空目录数: " + 空目录列表.length
输出 "非Markdown文件数: " + 非Markdown文件总数

IF 非Markdown文件总数 > 0 THEN
    输出 "非Markdown文件分类统计:"
    FOR EACH ext IN 按字母排序(扩展名分组.keys()) DO
        输出 "  - " + ext + ": " + 扩展名分组[ext].length + " 个"
    END FOR
END IF

输出 "总清理任务数: " + (多余文档列表.length + 空目录列表.length + 非Markdown文件总数)

// 10. 传递数据给后续 Stage
传递:
    - {CODE_ROOT}
    - {AIDOC_ROOT}
    - 源代码文件列表
    - 文档文件列表
    - 多余文档列表
    - 空目录列表
    - 非Markdown文件列表
    - 扩展名分组
```

---

## Stage 1: 删除多余文档（Delete Redundant Documents）

**目标**: 列出没有对应源代码的 `.md` 文件，等待用户确认后再删除

**执行时机**: Stage 0 完成之后，等待用户确认

**伪代码流程**:

```
// ========== Stage 1: 删除多余文档 ==========

// 第 1 步：从 Stage 0 获取多余文档列表
多余文档列表 = 从 Stage 0 获取 "多余文档列表"
{AIDOC_ROOT} = 从 Stage 0 获取 "{AIDOC_ROOT}"

// 第 2 步：索引文件保护（安全检查）
索引文件集合 = ["README.md", "INDEX.md", "SUMMARY.md", "GUIDE.md"]
受保护文档列表 = []
待删除文档列表 = []

FOR EACH doc IN 多余文档列表 DO
    doc文件名 = 获取文件名(doc文档路径)
    IF doc文件名 在 索引文件集合 THEN
        添加到 受保护文档列表: doc
    ELSE
        添加到 待删除文档列表: doc
    END IF
END FOR

// 第 3 步：展示列表给用户
输出分隔线和标题 "多余文档文件列表（待确认删除）"
FOR EACH doc IN 按路径排序(待删除文档列表) DO
    输出 "  - " + doc文档路径
END FOR

IF 受保护文档列表.length > 0 THEN
    输出 "受保护的索引文件（不会删除）:"
    FOR EACH doc IN 受保护文档列表 DO
        输出 "  - " + doc文档路径
    END FOR
END IF

// 第 4 步：用户确认
用户确认 = 询问用户 "是否确认删除以上待删除文档？（yes/no）"
IF 用户确认 != "yes" THEN
    输出 "用户取消删除操作"
    跳过此 Stage
END IF

// 第 5 步：执行删除操作
输出分隔线和标题 "开始删除多余文档"
成功计数 = 0
失败计数 = 0
删除结果详情 = []

FOR EACH doc IN 待删除文档列表 DO
    文件绝对路径 = {AIDOC_ROOT} + "/" + doc文档路径
    结果信息 = {
        文件路径: doc文档路径,
        状态: "",
        错误信息: ""
    }

    IF 文件绝对路径 存在 THEN
        TRY
            删除文件(文件绝对路径)
            成功计数 = 成功计数 + 1
            结果信息.状态 = "成功"
        CATCH 异常 e
            失败计数 = 失败计数 + 1
            结果信息.状态 = "失败"
            结果信息.错误信息 = e.message
        END TRY
    ELSE
        失败计数 = 失败计数 + 1
        结果信息.状态 = "失败"
        结果信息.错误信息 = "文件不存在"
    END IF

    添加到 删除结果详情: 结果信息
END FOR

// 第 6 步：输出删除报告
输出分隔线和标题 "多余文档删除报告"
输出 "总删除任务数: " + 待删除文档列表.length
输出 "成功数: " + 成功计数
输出 "失败数: " + 失败计数
输出 "跳过索引文件数: " + 受保护文档列表.length

IF 失败计数 > 0 THEN
    输出 "失败详情:"
    FOR EACH result IN 删除结果详情 WHERE result.状态 == "失败" DO
        输出 "  - " + result.文件路径 + ": " + result.错误信息
    END FOR
END IF

// 第 7 步：传递结果给后续 Stage
传递:
    - Stage1删除结果详情 = 删除结果详情
    - Stage1成功计数 = 成功计数
    - Stage1失败计数 = 失败计数
```

---

## Stage 2: 删除空目录（Delete Empty Directories）

**目标**: 列出文档目录中没有文档文件的空子目录，等待用户确认后再删除

**执行时机**: Stage 1 完成之后，等待用户确认

**伪代码流程**:

```
// ========== Stage 2: 删除空目录 ==========

// 第 1 步：从 Stage 0 获取空目录列表
空目录列表 = 从 Stage 0 获取 "空目录列表"
{AIDOC_ROOT} = 从 Stage 0 获取 "{AIDOC_ROOT}"

// 第 2 步：展示列表给用户
输出分隔线和标题 "空目录列表（待确认删除）"
FOR EACH dir IN 按路径排序(空目录列表) DO
    输出 "  - " + dir目录路径
END FOR

// 第 3 步：用户确认
用户确认 = 询问用户 "是否确认删除以上空目录？（yes/no）"
IF 用户确认 != "yes" THEN
    输出 "用户取消删除操作"
    跳过此 Stage
END IF

// 第 4 步：执行删除操作
输出分隔线和标题 "开始删除空目录"
成功计数 = 0
失败计数 = 0
删除结果详情 = []

FOR EACH dir IN 空目录列表 DO
    目录绝对路径 = {AIDOC_ROOT} + "/" + dir目录路径
    结果信息 = {
        目录路径: dir目录路径,
        状态: "",
        错误信息: ""
    }

    IF 目录绝对路径 存在 THEN
        IF 目录为空(目录绝对路径) THEN
            TRY
                删除目录(目录绝对路径)
                成功计数 = 成功计数 + 1
                结果信息.状态 = "成功"
            CATCH 异常 e
                失败计数 = 失败计数 + 1
                结果信息.状态 = "失败"
                结果信息.错误信息 = e.message
            END TRY
        ELSE
            失败计数 = 失败计数 + 1
            结果信息.状态 = "失败"
            结果信息.错误信息 = "目录不为空"
        END IF
    ELSE
        失败计数 = 失败计数 + 1
        结果信息.状态 = "失败"
        结果信息.错误信息 = "目录不存在"
    END IF

    添加到 删除结果详情: 结果信息
END FOR

// 第 5 步：输出删除报告
输出分隔线和标题 "空目录删除报告"
输出 "总删除任务数: " + 空目录列表.length
输出 "成功数: " + 成功计数
输出 "失败数: " + 失败计数

IF 失败计数 > 0 THEN
    输出 "失败详情:"
    FOR EACH result IN 删除结果详情 WHERE result.状态 == "失败" DO
        输出 "  - " + result.目录路径 + ": " + result.错误信息
    END FOR
END IF

// 第 6 步：传递结果给后续 Stage
传递:
    - Stage2删除结果详情 = 删除结果详情
    - Stage2成功计数 = 成功计数
    - Stage2失败计数 = 失败计数
```

---

## Stage 3: 移除非 Markdown 文件（Remove Non-Markdown Files）

**目标**: 按扩展名列出文档目录中所有非 `.md` 格式的文件，让用户选择要删除的扩展名类型

**执行时机**: Stage 2 完成之后，等待用户确认

**伪代码流程**:

```
// ========== Stage 3: 移除非 Markdown 文件 ==========

// 第 1 步：从 Stage 0 获取非 Markdown 文件列表
扩展名分组 = 从 Stage 0 获取 "扩展名分组"
{AIDOC_ROOT} = 从 Stage 0 获取 "{AIDOC_ROOT}"

// 第 2 步：展示扩展名分组统计
输出分隔线和标题 "非 Markdown 文件统计（按扩展名分组）"
FOR EACH ext IN 按字母排序(扩展名分组.keys()) DO
    文件列表 = 扩展名分组[ext]
    输出 ext + ": " + 文件列表.length + " 个文件"
    FOR EACH file IN 按路径排序(文件列表) DO
        输出 "  - " + file文件路径
    END FOR
END FOR

// 第 3 步：用户选择要删除的扩展名
输出分隔线
输出 "可选扩展名列表:"
FOR EACH ext IN 按字母排序(扩展名分组.keys()) DO
    输出 "  - " + ext
END FOR

用户选择 = 询问用户 "请输入要删除的扩展名（用逗号分隔，或输入 all 删除所有，或输入 skip 跳过）"
IF 用户选择 == "skip" THEN
    输出 "用户跳过非 Markdown 文件删除"
    跳过此 Stage
END IF

// 第 4 步：解析用户选择
待删除扩展名列表 = []

IF 用户选择 == "all" THEN
    待删除扩展名列表 = 按字母排序(扩展名分组.keys())
ELSE
    // 解析逗号分隔的扩展名
    扩展名数组 = 用户选择.split(",")
    FOR EACH ext IN 扩展名数组 DO
        ext = 去除首尾空格(ext)
        IF ext 在 扩展名分组.keys() THEN
            IF ext 不在 待删除扩展名列表 THEN
                添加到 待删除扩展名列表: ext
            END IF
        ELSE
            输出 "警告: 扩展名 '" + ext + "' 无效，已跳过"
        END IF
    END FOR
END IF

// 第 5 步：构建待删除文件列表
待删除文件列表 = []
FOR EACH ext IN 待删除扩展名列表 DO
    FOR EACH file IN 扩展名分组[ext] DO
        添加到 待删除文件列表:
            文件路径 = file文件路径
            绝对路径 = file绝对路径
            扩展名 = ext
    END FOR
END FOR

// 第 6 步：用户最终确认
输出分隔线和标题 "待删除文件确认"
输出 "待删除文件数: " + 待删除文件列表.length
输出 "涉及的扩展名: " + 待删除扩展名列表.join(", ")

用户确认 = 询问用户 "是否确认删除以上文件？（yes/no）"
IF 用户确认 != "yes" THEN
    输出 "用户取消删除操作"
    跳过此 Stage
END IF

// 第 7 步：执行删除操作
输出分隔线和标题 "开始删除非 Markdown 文件"
成功计数 = 0
失败计数 = 0
删除结果详情 = []
按扩展名统计 = {}

FOR EACH ext IN 待删除扩展名列表 DO
    按扩展名统计[ext] = {
        总数: 0,
        删除数: 0,
        失败数: 0
    }
END FOR

FOR EACH file IN 待删除文件列表 DO
    按扩展名统计[file扩展名].总数 = 按扩展名统计[file扩展名].总数 + 1

    结果信息 = {
        文件路径: file文件路径,
        扩展名: file扩展名,
        状态: "",
        错误信息: ""
    }

    IF file绝对路径 存在 THEN
        TRY
            删除文件(file绝对路径)
            成功计数 = 成功计数 + 1
            按扩展名统计[file扩展名].删除数 = 按扩展名统计[file扩展名].删除数 + 1
            结果信息.状态 = "成功"
        CATCH 异常 e
            失败计数 = 失败计数 + 1
            按扩展名统计[file扩展名].失败数 = 按扩展名统计[file扩展名].失败数 + 1
            结果信息.状态 = "失败"
            结果信息.错误信息 = e.message
        END TRY
    ELSE
        失败计数 = 失败计数 + 1
        按扩展名统计[file扩展名].失败数 = 按扩展名统计[file扩展名].失败数 + 1
        结果信息.状态 = "失败"
        结果信息.错误信息 = "文件不存在"
    END IF

    添加到 删除结果详情: 结果信息
END FOR

// 第 8 步：输出删除报告
输出分隔线和标题 "非 Markdown 文件移除报告"
输出 "用户选择的扩展名: " + 待删除扩展名列表.join(", ")
输出 "文件数: " + 待删除文件列表.length
输出 "总移除任务数: " + 待删除文件列表.length
输出 "成功数: " + 成功计数
输出 "失败数: " + 失败计数

跳过扩展名列表 = []
FOR EACH ext IN 扩展名分组.keys() DO
    IF ext 不在 待删除扩展名列表 THEN
        添加到 跳过扩展名列表: ext
    END IF
END FOR

IF 跳过扩展名列表.length > 0 THEN
    输出 "跳过的扩展名: " + 跳过扩展名列表.join(", ")
END IF

输出 "按扩展名统计:"
FOR EACH ext IN 按字母排序(按扩展名统计.keys()) DO
    统计 = 按扩展名统计[ext]
    输出 "  - " + ext + ": 总数=" + 统计.总数 + ", 删除数=" + 统计.删除数 + ", 失败数=" + 统计.失败数
END FOR

IF 失败计数 > 0 THEN
    输出 "失败详情:"
    FOR EACH result IN 删除结果详情 WHERE result.状态 == "失败" DO
        输出 "  - " + result.文件路径 + ": " + result.错误信息
    END FOR
END IF

// 第 9 步：传递结果给后续 Stage
传递:
    - Stage3删除结果详情 = 删除结果详情
    - Stage3成功计数 = 成功计数
    - Stage3失败计数 = 失败计数
    - Stage3按扩展名统计 = 按扩展名统计
```

---

## Stage 4: 最终验证与报告生成（Final Verification & Report Generation）

**目标**: 重新扫描文档目录，验证清理操作是否完整，生成最终的综合报告

**执行时机**: Stage 3 完成之后

**伪代码流程**:

```
// ========== Stage 4: 最终验证与报告生成 ==========

// 第 1 步：重新扫描文档目录
{CODE_ROOT} = 从 Stage 0 获取 "{CODE_ROOT}"
{AIDOC_ROOT} = 从 Stage 0 获取 "{AIDOC_ROOT}"

// 重新扫描源代码文件
重新扫描_源代码文件列表 = []
FOR EACH file IN 递归遍历({CODE_ROOT}) DO
    IF file 不是 AiDoc目录 AND file扩展名 == ".cs" THEN
        添加到 重新扫描_源代码文件列表:
            文件路径 = 相对路径(file, {CODE_ROOT})
    END IF
END FOR

// 重新扫描文档文件
重新扫描_文档文件列表 = []
FOR EACH file IN 递归遍历({AIDOC_ROOT}) DO
    IF file扩展名 == ".md" THEN
        添加到 重新扫描_文档文件列表:
            文件路径 = 相对路径(file, {AIDOC_ROOT})
    END IF
END FOR

// 重新扫描非 Markdown 文件
重新扫描_非Markdown文件列表 = []
FOR EACH file IN 递归遍历({AIDOC_ROOT}) DO
    IF file扩展名 != ".md" AND file扩展名 != "" THEN
        添加到 重新扫描_非Markdown文件列表:
            文件路径 = 相对路径(file, {AIDOC_ROOT})
            扩展名 = file扩展名
    END IF
END FOR

// 重新扫描空目录
重新扫描_空目录列表 = []
FOR EACH dir IN 自底向上遍历({AIDOC_ROOT}) DO
    IF 目录为空(dir) THEN
        添加到 重新扫描_空目录列表:
            目录路径 = 相对路径(dir, {AIDOC_ROOT})
    END IF
END FOR

// 第 2 步：验证清理结果，查找残留的多余文档
索引文件集合 = ["README.md", "INDEX.md", "SUMMARY.md", "GUIDE.md"]
残留_多余文档列表 = []
FOR EACH doc IN 重新扫描_文档文件列表 DO
    doc文件名 = 获取文件名(doc文件路径)
    IF doc文件名 不在 索引文件集合 THEN
        源代码路径 = 将doc路径中的.md替换为.cs
        源代码绝对路径 = {CODE_ROOT} + "/" + 源代码路径
        IF 源代码绝对路径 不存在 THEN
            添加到 残留_多余文档列表:
                文档路径 = doc文件路径
        END IF
    END IF
END FOR

// 第 3 步：获取之前各阶段的统计数据
Stage0_源代码文件数 = 从 Stage 0 获取 "源代码文件列表".length
Stage0_文档文件数 = 从 Stage 0 获取 "文档文件列表".length
Stage0_非Markdown文件数 = 从 Stage 0 获取 "非Markdown文件总数"
Stage0_空目录数 = 从 Stage 0 获取 "空目录列表".length
Stage0_多余文档数 = 从 Stage 0 获取 "多余文档列表".length

Stage1_成功计数 = 从 Stage 1 获取 "Stage1成功计数"
Stage1_失败计数 = 从 Stage 1 获取 "Stage1失败计数"

Stage2_成功计数 = 从 Stage 2 获取 "Stage2成功计数"
Stage2_失败计数 = 从 Stage 2 获取 "Stage2失败计数"

Stage3_成功计数 = 从 Stage 3 获取 "Stage3成功计数"
Stage3_失败计数 = 从 Stage 3 获取 "Stage3失败计数"

// 第 4 步：计算清理效果
清理前_文档文件数 = Stage0_文档文件数
清理后_文档文件数 = 重新扫描_文档文件列表.length
删除_文档文件数 = 清理前_文档文件数 - 清理后_文档文件数
清理率 = 删除_文档文件数 / 清理前_文档文件数 * 100

// 第 5 步：生成遗留问题清单
遗留问题列表 = []

// 检查多余文档
FOR EACH doc IN 残留_多余文档列表 DO
    添加到 遗留问题列表:
        问题类型 = "多余文档"
        描述 = "没有对应源代码的文档文件"
        位置 = doc文档路径
        严重程度 = "中"
        建议 = "手动删除或确认是否需要保留"
END FOR

// 检查非 Markdown 文件
IF 重新扫描_非Markdown文件列表.length > 0 THEN
    FOR EACH file IN 重新扫描_非Markdown文件列表 DO
        添加到 遗留问题列表:
            问题类型 = "非 Markdown 文件"
            描述 = "文档目录中的非 .md 文件"
            位置 = file文件路径 + " (" + file扩展名 + ")"
            严重程度 = "低"
            建议 = "手动检查并删除不需要的文件"
    END FOR
END IF

// 检查空目录
FOR EACH dir IN 重新扫描_空目录列表 DO
    添加到 遗留问题列表:
        问题类型 = "空目录"
        描述 = "文档目录中的空目录"
        位置 = dir目录路径
        严重程度 = "低"
        建议 = "手动删除空目录"
END FOR

// 第 6 步：输出最终报告
输出分隔线和标题 "AiDoc 清理最终报告"
输出 "执行时间: " + 当前时间()
输出 "代码根目录: " + {CODE_ROOT}
输出 "文档根目录: " + {AIDOC_ROOT}

// 输出各阶段执行汇总
输出分隔线
输出 "各阶段执行汇总:"
输出 "Stage 0 - 环境检测与扫描:"
输出 "  - 源代码文件数: " + Stage0_源代码文件数
输出 "  - 文档文件数: " + Stage0_文档文件数
输出 "  - 多余文档数: " + Stage0_多余文档数
输出 "  - 空目录数: " + Stage0_空目录数
输出 "  - 非Markdown文件数: " + Stage0_非Markdown文件数

输出 "Stage 1 - 删除多余文档:"
输出 "  - 总删除任务数: " + (Stage1_成功计数 + Stage1_失败计数)
输出 "  - 成功数: " + Stage1_成功计数
输出 "  - 失败数: " + Stage1_失败计数

输出 "Stage 2 - 删除空目录:"
输出 "  - 总删除任务数: " + (Stage2_成功计数 + Stage2_失败计数)
输出 "  - 成功数: " + Stage2_成功计数
输出 "  - 失败数: " + Stage2_失败计数

输出 "Stage 3 - 移除非 Markdown 文件:"
输出 "  - 总移除任务数: " + (Stage3_成功计数 + Stage3_失败计数)
输出 "  - 成功数: " + Stage3_成功计数
输出 "  - 失败数: " + Stage3_失败计数

// 输出最终验证结果
输出分隔线
输出 "最终验证结果:"
输出 "  - 重新扫描文档文件数: " + 清理后_文档文件数
输出 "  - 删除的文档文件数: " + 删除_文档文件数
输出 "  - 清理率: " + 清理率.toFixed(2) + "%"
输出 "  - 残留非Markdown文件数: " + 重新扫描_非Markdown文件列表.length
输出 "  - 残留空目录数: " + 重新扫描_空目录列表.length
输出 "  - 残留多余文档数: " + 残留_多余文档列表.length

// 输出遗留问题清单
输出分隔线
输出 "遗留问题清单:"
IF 遗留问题列表.length == 0 THEN
    输出 "  无遗留问题，清理完成！"
ELSE
    FOR i FROM 1 TO 遗留问题列表.length DO
        问题 = 遗留问题列表[i - 1]
        输出 "  [" + i + "] " + 问题.问题类型 + " (" + 问题.严重程度 + ")"
        输出 "      描述: " + 问题.描述
        输出 "      位置: " + 问题.位置
        输出 "      建议: " + 问题.建议
    END FOR
END IF

// 输出执行总结
输出分隔线
输出 "执行总结:"
总操作数 = Stage1_成功计数 + Stage1_失败计数 + Stage2_成功计数 + Stage2_失败计数 + Stage3_成功计数 + Stage3_失败计数
总成功数 = Stage1_成功计数 + Stage2_成功计数 + Stage3_成功计数
总失败数 = Stage1_失败计数 + Stage2_失败计数 + Stage3_失败计数
成功率 = 总成功数 / 总操作数 * 100

输出 "  总操作数: " + 总操作数
输出 "  成功操作数: " + 总成功数
输出 "  失败操作数: " + 总失败数
输出 "  成功率: " + 成功率.toFixed(2) + "%"

输出 "各阶段成功/失败汇总:"
输出 "  - Stage 1: 成功 " + Stage1_成功计数 + " / 失败 " + Stage1_失败计数
输出 "  - Stage 2: 成功 " + Stage2_成功计数 + " / 失败 " + Stage2_失败计数
输出 "  - Stage 3: 成功 " + Stage3_成功计数 + " / 失败 " + Stage3_失败计数

输出 "建议:"
IF 总失败数 > 0 OR 遗留问题列表.length > 0 THEN
    输出 "  - 请检查失败操作的详情，并手动处理遗留问题"
    输出 "  - 建议再次运行清理操作以完成所有清理任务"
ELSE
    输出 "  - 文档清理完成，目录结构已与源代码目录结构一致"
END IF

输出报告结束标记 "========== AiDoc 清理完成 =========="
```

---

## 使用示例（Usage Examples）

### 示例 1: 完整清理流程

**用户输入**:
```
清理 AiDoc 文档目录
```

**执行流程**:
1. Stage 0: 环境检测与扫描
2. Stage 1: 删除多余文档（需用户确认）
3. Stage 2: 删除空目录（需用户确认）
4. Stage 3: 移除非 Markdown 文件（需用户确认）
5. Stage 4: 最终验证与报告生成

### 示例 2: 仅扫描不删除

**用户输入**:
```
扫描 AiDoc 文档目录
```

**执行流程**:
1. Stage 0: 环境检测与扫描
2. 输出扫描结果，不执行删除操作

### 示例 3: 仅删除指定类型

**用户输入**:
```
删除 AiDoc 文档目录中的 .ai 文件
```

**执行流程**:
1. Stage 0: 环境检测与扫描
2. Stage 3: 移除非 Markdown 文件（仅选择 .ai 扩展名）
3. Stage 4: 最终验证与报告生成
