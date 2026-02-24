---
description: 
alwaysApply: true
enabled: false
updatedAt: 2026-02-05T09:43:32.893Z
provider: 
---

你是一个专业的Lua开发助手，所有Lua代码必须严格遵循以下编码规范。

## 规范等级说明
- **必须（Mandatory）** 级别要求编码者严格按照规范的编码格式编写
- **推荐（Preferable）** 级别希望编码者按照规范编写，但不强制要求

## 基本原则
- 优先考虑代码的可读性与可维护性
- 保持与宿主语言（如C、C++）程序的命名和字符串定义规则统一
- 整个项目的编码风格必须保持一致

## 1. 表规范

**推荐** 在表创建时，利用构造器对其属性进行赋值
```lua
-- good
local user = {
    name = "Robin",
    level = 56,
    grade = "gold"
}
```

**推荐** 在表定义的外部定义函数
**必须** 在定义函数过程中，引用自身时使用`self`
```lua
-- good
local file_path = {}

function file_path:full_path()
    return string.format("%s%s%s", self.current_dir, "/", self.file_name)
end
```

## 2. 属性访问

**推荐** 访问已知属性时，使用`.`符号
**推荐** 利用变量访问属性或列表时，使用`[]`符号

## 3. 函数规范

**推荐** 尽量用多个简单函数替代大型、复杂函数
**必须** 函数调用不能省略括号
```lua
-- bad
foo "param"
bar { user_id = 1 }

-- good
foo("param")
bar({ user_id = 1 })
```

**推荐** 尽量不要用变量定义的方式定义函数
```lua
-- good
local function battle_info(user_id, battle_id)
    -- ...stuff...
end
```

**必须** 不要用`arg`作为参数名，在低版本Lua中`arg`作为参数对象存在
**推荐** 尽早验证条件，并尽早返回结果
**推荐** 函数中的嵌套尽量控制在`3-4`层
**推荐** 函数定义与调用过程中，**冒号**与**点**保持一致

## 4. 变量规范

**必须** 避免滥用**全局变量**或**全局函数**。尽量用`local`定义变量
```lua
-- good
local friend_num = get_friend_num()
```

**推荐** 当前文件的**全局变量**或**函数**，建议前置`local`，可以提升访问性能
```lua
local xpcall = _G.xpcall
local select = _G.select
local pairs = _G.pairs
local ipairs = _G.ipairs
local table_insert = _G.table.insert
```

## 5. 空白规范

**推荐** 使用tabs（空格字符）设置为`4`个空格
**必须** 赋值操作符、比较操作符、算术操作符、逻辑运算符等二元操作符的前后应当加空格
```lua
-- good
local score = 1
score = score - 1
score = score * 1
local title = "str1" .. "str2"
```

**必须** 逗号之前避免使用空格，逗号之后需要使用空格
```lua
-- good
local array = { 1, 2, 3 }
```

**必须** 在多行代码块之间用一空行隔离
**推荐** 用一空行作为文件结尾
**推荐** 在行尾删除不必要的空格

## 6. 逗号和分号

**必须** 逗号后置
```lua
-- good
local user = {
    name = "Robin",
    level = 56,
    grade = "gold"
}
```

**必须** 不要通过`;`对语句分行，一行只能有一个语句

## 7. 条件表达式

**推荐** 除非需要明确`false`与`nil`，否则直接利用条件判断即可

## 8. 类型转换

**必须** 在语句的开头，利用内置函数进行类型转换（`tostring`, `tonumber`, etc.）
**必须** 如果不需要字符连接，字符串类型转换使用`tostring`
**必须** 数字类型转换使用`tonumber`
```lua
-- good
local total_score = tostring(review_score)
local level = tonumber(input_level)
```

## 9. 命名规范

**必须** 避免使用单字母来命名函数或变量，命名时遵从**见文知意**原则
**必须** 循环中忽略的变量使用`_`
**推荐** 循环中的索引命名时尽量可以代表其实际含义
**推荐** 对于布尔值或返回值为布尔值的函数命名时，请使用`is`或者`has`为前缀
**推荐** 类成员私有变量或方法加`_`前缀
**推荐** 全局的常量命名，均用大写，区分普通变量

## 10. 注释规范

**推荐** 对变量定义时，可以使用`--`在行末对其注释
**推荐** 对语句块进行注释时，使用`--`进行单行注释，在注释之前放一个空行（除非它在块的第一行）
**必须** 对大段内容进行注释时，使用`--[[]]`
**推荐** 使用`FIXME`、`TODO`、`XXX`开始注释可以帮助其他开发人员快速了解相应代码
**推荐** 关键函数应添加相应注释
**推荐** 每个模块应以注释开头

## 11. 日志规范

**必须** 日志需区分等级，方便发布时进行开关配置
```lua
function log_info() end
function log_debug() end  
function log_warning() end
function log_error() end
```

## 12. 模块规范

**推荐** 模块应返回表或函数
**推荐** 模块不应使用全局命名空间，且应为一个闭包
**推荐** 命名时尽量能体现出该文件是一个模块

## 13. 文件结构

**推荐** 文件以小写字母命名

## 14. 编码方式

**必须** 源文件编码需统一使用`UTF-8`编码
**必须** 避免不同操作系统对文件换行处理的方式不同，一律使用`LF`(`\n`)

## 编码技巧

### 字符串拼接
**推荐** 字符串格式化拼接时，推荐使用`string.format`
**必须** 对于循环拼接字符串场景，使用`table.concat`
```lua
-- good
res_str = table.concat(sub_str)
```

### 表的操作
**推荐** 避免`array`与`hash`混用
**必须** 禁止显式指定`array`下标从`0`开始
**必须** 使用`next`判断空表
**必须** `array`部分元素移除用`remove`, `hash`部分元素移除直接置`nil`
**必须** 计算表中元素个数时，需要考虑`nil`值的影响，建议设置字段`n`来统计其长度
**必须** `#tb`仅适用于`array`，`hash`禁止使用`#`关键字来获取表长度
**必须** `ipairs`、`#`关键字搭配`for`循环只能用来遍历`array`，而`pairs`或者`next`可以遍历任意集合
**必须** 表遍历过程中不能对其**新增元素**，但可以修改表元素或通过`nil`来删除表数据
**推荐** `array`的`append`操作，推荐使用`tb[#tb + 1] = value`

### 可变参数
**推荐** 使用`select`关键字获取可变参数的参数个数
**推荐** 如果需要将可变参数暂时保存，再使用保存的可变参数调用其它函数，需要先`pack`可变参数，再使用`unpack`

### 面向对象
**推荐** 合理使用元表，将`table`概念扩展为类似`class`的概念，实现封装和继承
**推荐** 公有成员函数以`item:foo`形式定义
**推荐** 私有成员函数以**局部函数**定义

### 内存管理
**推荐** 尽量使用`require`机制加载文件，避免使用`dofile`、`dostring`
**推荐** 尽量**按需**`require`
**推荐** 谨慎使用`string.gmatch`，频繁调用会导致`gc`压力增大
**推荐** 谨慎使用长字符串（长度超过`40`）
**推荐** 由于Lua的`gc`机制，尽少使用**弱表**，尤其是容量很大的弱表

### 额外规则
**必须** 获取父节点时，使用`self:GetParentActor()`，可以直接使用不需要cast to转换
示例：
    local WishingActor = self:GetParentActor()
    if UE.IsValid(WishingActor) and WishingActor.bInYueYaArea == false then
        UAEClosure_PlayerStaticFunction.LoadWeatherSequence(PC, self.WeatherSequence, self.BlendParam)
    end