---
name: exportbp2json
description: 和平精英项目组蓝图转json工具。通过将蓝图转成特定的json格式，用来辅助查看蓝图信息、AI生成代码。
allowed-tools: python
---

## 输入参数
- 蓝图路径：形如 WidgetBlueprint'/Game/UMG/WebViewTestUI.WebViewTestUI'
- 输出路径（可选）：指定JSON文件的输出路径，如不指定则输出到蓝图同目录

## 前置条件
1. 已安装并配置Unreal Engine开发环境
2. UE4Editor-Cmd.exe已在系统PATH环境变量中
3. 已安装必要的Python依赖库
4. exportbp2ue.py和exportue2json.py脚本已存在于可访问路径

## 执行流程
### 阶段一：调用UE工具，将蓝图导出为文本格式
1. 验证蓝图路径是否存在且格式正确
2. 执行命令：`python exportbp2ue.py -f exportbp.py -a "蓝图路径"`
3. 检查脚本返回码：
   - 如果返回0：继续执行阶段二
   - 如果返回非0：记录错误信息，流程终止

### 阶段二：调用本地脚本，将文本格式转换为json格式
1. 获取阶段一生成的文本文件路径
2. 执行命令：`python exportue2json.py "蓝图文本文件路径"`
3. 检查脚本返回码：
   - 如果返回0：流程执行成功
   - 如果返回非0：记录错误信息，流程终止

## 输出结果
- 成功时：在脚本同目录生成对应的JSON文件
- 失败时：返回错误信息和错误码

## 错误处理
1. 蓝图路径不存在或格式错误
2. UE4Editor-Cmd.exe执行失败
3. 蓝图文件损坏或无法解析
4. 输出路径无写入权限
5. Python脚本依赖库缺失

## 执行说明
- 执行过程完全自动化，不与用户进行交互
- 任一阶段失败即终止整个流程
- 所有错误信息会记录到日志文件中
- 支持批量处理（通过外部调度实现）

## 示例
输入：WidgetBlueprint'/Game/UMG/LoginUI.LoginUI'
输出：在脚本同目录生成LoginUI.json文件