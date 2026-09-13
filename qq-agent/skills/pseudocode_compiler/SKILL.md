---
name: pseudocode_compiler
description: "CAIE 伪代码编译器。将伪代码编译为 Python 并执行，支持语法检查、INPUT 预注入、FUNCTION/PROCEDURE 参数化调用。"
metadata:
  {
    "builtin_skill_version": "1.0",
    "copaw":
      {
        "emoji": "🔧",
        "requires": {}
      }
  }
---

# CAIE Pseudocode Compiler

工作目录下有两个核心脚本：

- `compiler_tool.py` — 编译器的命令行包装（254行）
- `run_compiler.py` — 辅助脚本，从 `input_code.txt` 读取代码并调用 compiler_tool.py

## 使用方法

**绝不** 直接传伪代码到命令行参数（会有 shell 转义问题）。**始终** 先写文件再调用：

```
步骤 1: write_file(path="input_code.txt", content="伪代码内容")
步骤 2: execute_shell_command(command="python run_compiler.py")
```

### 带输入值调用

当用户提供了 INPUT 变量或 FUNCTION/PROCEDURE 参数值：

```
execute_shell_command(command="python run_compiler.py --inputs {\"变量名\":\"值\"}")
```

## 返回格式

JSON 格式，关键字段：

| 字段 | 说明 |
|------|------|
| `success` | 编译是否成功 |
| `action` | `executed` / `need_input` / `need_params` / `compile_only` |
| `errors` | 错误列表（含行号） |
| `warnings` | 警告列表 |
| `python_code` | 生成的 Python 代码 |
| `has_input` | 是否含 INPUT 语句 |
| `input_vars` | INPUT 变量名列表 |
| `is_callable` | 是否是独立 FUNCTION/PROCEDURE |
| `callable_info` | 可调用信息（名称、参数、类型） |
| `INSTRUCTION` | LLM 必须遵循的指令 |
| `output` | 执行输出（action=executed 时） |

## 重要注意事项

- 返回 JSON 中若有 `INSTRUCTION` 字段，**必须严格遵循**
- Windows 环境，编码已处理（UTF-8）
- 编译器支持完整 CAIE 伪代码规范
