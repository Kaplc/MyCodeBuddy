---
name: lua-log-generator
description: 在UE4 Lua代码中使用print_dev智能添加日志打印功能。支持在关键位置插入print_dev日志语句,帮助调试和问题追踪。
---

# Lua-Log-Generator - Lua日志生成器

**核心目标**: 专门用于在UE4 Lua代码中使用 `print_dev()` 智能添加日志打印功能,遵循Lua代码规范,提供便捷的日志插入方式。

**重要说明**:
- **日志生成**: 由大模型（AI）根据代码上下文和规范文档智能生成
- **代码分析**: 分析代码逻辑,在关键位置自动插入 `print_dev()` 语句
- **规范遵循**: 严格遵循 Lua代码规范.md 中关于日志的规范
- **统一使用**: 仅使用 `print_dev()` 函数进行日志输出

---

## Stage 0: 环境检测与初始化(Environment Detection & Initialization)

**目标**: 检测当前Lua文件,分析代码结构,确定日志插入位置

**执行时机**: 所有其他 Stage 之前,必须首先执行

**伪代码流程**:

```
// ========== Stage 0: 环境检测与初始化 ==========

// 1. 加载 Lua 代码规范
加载 Lua代码规范.md 获取日志相关规范

// 2. 检测目标文件
IF 用户指定了文件路径 THEN
    target_file_path = 用户指定的文件路径
    确认文件存在
ELSE
    询问用户要处理的Lua文件路径
END IF

// 3. 读取目标文件内容
source_code = read_file_content(target_file_path)

// 4. 分析代码结构
函数列表 = extract_functions(source_code)
类/模块信息 = extract_classes_or_modules(source_code)
关键逻辑节点 = extract_critical_logic_points(source_code)

// 5. 生成日志插入建议
日志插入建议列表 = []
FOR EACH 函数 IN 函数列表 DO
    分析函数逻辑
    生成日志插入点建议:
        - 函数入口
        - 条件分支
        - 错误处理
        - 关键变量变化
END FOR

// 6. 输出分析结果
输出 "目标文件: " + target_file_path
输出 "检测到函数数量: " + 函数列表.length
输出 "建议添加日志位置: " + 日志插入建议列表.length + " 个"

// 传递数据给 Stage 1
传递:
    - target_file_path
    - source_code
    - 函数列表
    - 日志插入建议列表
```

---

## Stage 1: 日志生成策略选择(Log Generation Strategy Selection)

**目标**: 根据用户需求选择合适的日志生成策略

**执行时机**: Stage 0 完成环境检测和文件扫描之后

**伪代码流程**:

```
// ========== Stage 1: 日志生成策略选择 ==========

// 第 1 步: 分析用户需求
// 固定使用 print_dev() 日志函数
日志函数 = "print_dev"

IF 用户指定了函数名称 THEN
    目标函数列表 = [用户指定的函数名]
ELSE
    目标函数列表 = Stage 0 中的所有函数
END IF

// 第 2 步: 定义日志生成策略
策略配置 = {
    entry: {
        函数入口日志,
        格式: "ClassName:FunctionName start",
        描述: "记录函数调用"
    },
    exit: {
        函数出口日志,
        格式: "ClassName:FunctionName end",
        描述: "记录函数返回"
    },
    condition: {
        条件分支日志,
        格式: "ClassName:FunctionName condition result={result}",
        描述: "记录条件判断结果"
    },
    error: {
        错误处理日志,
        格式: "ClassName:FunctionName error: {error_info}",
        描述: "记录错误信息"
    },
    variable: {
        变量变化日志,
        格式: "ClassName:FunctionName var={var_name}={var_value}",
        描述: "记录关键变量变化"
    }
}

// 第 3 步: 选择目标策略
IF 用户指定了策略类型 THEN
    选择策略 = 用户指定的策略
ELSE
    选择策略 = ["entry", "error"]  // 默认添加入口和错误日志
END IF

// 第 4 步: 生成日志插入计划
日志插入计划 = []
FOR EACH 目标函数 IN 目标函数列表 DO
    FOR EACH 策略 IN 选择策略 DO
        日志插入位置 = find_insert_position(目标函数, 策略)
        IF 日志插入位置 THEN
            添加到 日志插入计划:
                function_name = 目标函数
                strategy = 策略
                insert_position = 日志插入位置
                log_content = generate_log_content(目标函数, 策略)
        END IF
    END FOR
END FOR

输出日志插入计划
```

---

## Stage 2: 执行日志插入(Execute Log Insertion)

**目标**: 在代码中实际插入日志语句

**执行时机**: Stage 1 完成策略选择之后

**伪代码流程**:

```
// ========== Stage 2: 执行日志插入 ==========

// 第 1 步: 按行号排序插入点
按 insert_position 对 日志插入计划 进行升序排序

// 第 2 步: 从后向前插入日志(避免行号偏移)
FOR i FROM 日志插入计划.length TO 1 DO
    plan = 日志插入计划[i]

    // 生成日志语句
    log_statement = generate_log_statement(plan)

    // 插入日志到指定位置
    source_code = insert_line_at_position(
        source_code,
        plan.insert_position,
        log_statement
    )

    输出 "已插入日志: " + plan.function_name + " (" + plan.strategy + ")"
END FOR

// 第 3 步: 写入文件
write_file_content(target_file_path, source_code)

// 第 4 步: 生成插入报告
输出日志插入报告:
    - 总插入日志数
    - 插入的函数列表
    - 每个日志的详细信息
```

---

## 日志生成规范(Log Generation Specifications)

**日志函数**: 统一使用 `print_dev()`

- **print_dev()** - 开发日志
   ```lua
   print_dev("ClassName:FunctionName message")
   ```

**日志格式规范**:

- **函数入口日志**: `print_dev("ClassName:FunctionName start")`
- **函数出口日志**: `print_dev("ClassName:FunctionName end")`
- **条件分支日志**: `print_dev("ClassName:FunctionName condition=" .. tostring(value))`
- **错误处理日志**: `print_dev("ClassName:FunctionName error: " .. tostring(error_info))`
- **变量跟踪日志**: `print_dev("ClassName:FunctionName var=" .. var_name .. "=" .. tostring(var_value))`
- **状态变更日志**: `print_dev("ClassName:FunctionName state changed from=" .. tostring(old) .. " to=" .. tostring(new))`

**日志插入原则**:

1. **关键位置优先**: 在函数入口、出口、条件判断、循环等关键位置添加日志
2. **错误处理必加**: 所有错误处理路径必须添加错误日志
3. **调试信息适度**: 避免过度添加日志,只记录关键信息
4. **格式统一**: 日志格式遵循统一规范,便于日志分析
5. **性能考虑**: 避免在性能敏感路径添加过多日志

---

## 使用示例(Usage Examples)

### 示例 1: 为单个函数添加入口和出口日志

**用户输入**:
```
为 WerewolfSignUPActor:ShowModeSelectUI 函数添加入口和出口日志
```

**执行流程**:
1. Stage 0: 读取文件,分析函数结构
2. Stage 1: 选择 entry 和 exit 策略
3. Stage 2: 在函数首尾添加日志
4. 输出插入结果

**生成结果**:
```lua
function WerewolfSignUPActor:ShowModeSelectUI(InParam)
    print_dev("WerewolfSignUPActor:ShowModeSelectUI start")
    local PC = InParam.PlayerController
    if PC then
        -- ... 原有代码 ...
    end
    print_dev("WerewolfSignUPActor:ShowModeSelectUI end")
end
```

### 示例 2: 为所有条件分支添加日志

**用户输入**:
```
为 LostTomb_TLog.StatisticsTrigger 函数的所有条件判断添加日志
```

**执行流程**:
1. Stage 0: 分析条件分支
2. Stage 1: 选择 condition 策略
3. Stage 2: 在每个 if 判断后添加日志
4. 输出插入结果

### 示例 3: 为错误处理添加日志

**用户输入**:
```
为当前文件的所有错误检查添加错误日志
```

**执行流程**:
1. Stage 0: 扫描所有错误检查代码
2. Stage 1: 选择 error 策略
3. Stage 2: 在所有返回 nil 的错误路径添加日志
4. 输出插入结果

### 示例 4: 批量为模块添加完整日志

**用户输入**:
```
为 WK_TaskComponent 模块的所有函数添加入口和错误日志
```

**执行流程**:
1. Stage 0: 扫描模块所有函数
2. Stage 1: 选择 entry 和 error 策略
3. Stage 2: 批量插入日志
4. 输出插入报告

---

## 注意事项(Important Notes)

**重要原则**:
- **最小侵入**: 日志插入应尽量不影响原有代码逻辑
- **可移除性**: 生成的日志应易于识别和移除
- **规范遵循**: 严格遵循 Lua代码规范.md 中的命名和格式规范
- **性能考虑**: 避免在循环或高频调用路径添加过多日志
- **安全检查**: 确保插入的日志不会导致语法错误

**生成日志的要求**:
1. **统一使用** `print_dev()` 作为唯一日志函数
2. 日志格式包含 类名:函数名 消息内容
3. 使用 `tostring()` 转换变量值
4. 使用 `string.format()` 进行格式化
5. 保持与项目现有日志风格一致

**特殊情况处理**:
- **已有日志**: 检查目标位置是否已有日志,避免重复
- **短函数**: 对于只有几行代码的函数,只添加入口日志
- **递归函数**: 避免添加会导致无限循环的日志
- **性能敏感路径**: 添加性能相关的日志时需要谨慎

**代码质量保证**:
- 插入日志后,确保代码可以正常运行
- 日志内容应有实际意义,避免无意义的日志
- 关键变量应记录其值,便于调试
- 错误日志应包含足够的错误信息

---

## Lua 代码规范引用

**日志规范(必须)**:
- **统一使用** `print_dev()` 作为唯一的开发日志函数
- 日志格式统一,便于分析和过滤

**命名规范(必须)**:
- 避免使用单字母命名
- 遵循"见文知意"原则
- 函数命名使用 `ClassName:FunctionName` 格式

**字符串拼接(推荐)**:
- 字符串格式化使用 `string.format()`
- 变量转换使用 `tostring()`

> 详细规范内容请参考 [Lua代码规范.md](./Lua代码规范.md) 文件
