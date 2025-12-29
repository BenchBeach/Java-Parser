# get_context.py 使用文档

## 概述

`get_context.py` 是一个 Java 函数上下文提取工具，用于分析指定 Java 方法的上下文信息，包括：

- 待测方法所在类的完整信息（类名、字段、方法签名）
- 待测方法的完整方法体
- 返回值类型对应的类信息（如果是项目内的类）
- 参数类型对应的类信息（如果是项目内的类）
- 生成用于大模型理解的结构化文本 `context_prompt`

## 安装依赖

```bash
pip install loguru tree-sitter tree-sitter-java
```

## 命令行用法

```bash
python get_context.py <project_root> <main_src> <test_src> <method_key> [--load LOAD] [--output OUTPUT]
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `project_root` | 是 | 项目根路径 |
| `main_src` | 是 | 业务代码路径（如 `src/main/java`） |
| `test_src` | 是 | 测试代码路径（如 `src/test/java`） |
| `method_key` | 是 | 待分析方法的完整签名，格式：`类FQN#方法签名` |
| `--load` | 否 | 已保存的二进制解析文件路径（加速重复分析） |
| `--output` | 否 | 结果输出到指定 JSON 文件（不指定则打印到终端） |

### method_key 格式说明

方法签名格式为：`完整类名#方法名(参数类型1,参数类型2,...)`

示例：
- `org.apache.commons.math4.core.jdkmath.AccurateMath#cosh(double)`
- `org.apache.commons.math4.core.jdkmath.AccurateMath.Split#multiply(Split)`
- `com.example.UserService#findUserById(java.lang.Long)`

## 使用示例

### 基本用法

```bash
python get_context.py \
  "/path/to/project" \
  "/path/to/project/src/main/java" \
  "/path/to/project/src/test/java" \
  "org.apache.commons.math4.core.jdkmath.AccurateMath#cosh(double)"
```

### 输出到文件

```bash
python get_context.py \
  "/path/to/project" \
  "/path/to/project/src/main/java" \
  "/path/to/project/src/test/java" \
  "org.apache.commons.math4.core.jdkmath.AccurateMath.Split#multiply(Split)" \
  --output result.json
```

### 使用缓存加速

首次解析后可使用 `parser_main.py` 保存解析结果，后续通过 `--load` 加载：

```bash
# 首次解析并保存
python parser_main.py /path/to/project /path/to/main /path/to/test --save project.pkl

# 后续使用缓存
python get_context.py /path/to/project /path/to/main /path/to/test "Class#method()" --load project.pkl
```

## 输出 JSON 结构

```json
{
  "class_info": {
    "class_name": "Split",
    "fqn": "org.apache.commons.math4.core.jdkmath.AccurateMath.Split",
    "fields": [
      {
        "name": "high",
        "type": "double",
        "modifiers": ["private", "final"],
        "annotations": [],
        "raw_text": "private final double high;",
        "value": null
      }
    ],
    "methods": [
      {
        "name": "multiply",
        "signature": "public Split multiply(Split)",
        "return_type": "Split",
        "modifiers": ["public"],
        "annotations": [],
        "parameters": [
          {
            "name": "b",
            "type": "Split",
            "annotations": []
          }
        ],
        "raw_text": "public Split multiply(final Split b) { ... }"
      }
    ]
  },
  "method_signature": "multiply(Split)",
  "method_body": "public Split multiply(final Split b) { ... }",
  "parameters": [],
  "return_type": "Split",
  "parameter_class_info": [
    {
      "param": "b",
      "class_info": { ... }
    }
  ],
  "return_class_info": { ... },
  "context_prompt": "// This is the context of method under test\n..."
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `class_info` | object | 待测方法所在类的完整信息 |
| `method_signature` | string | 方法签名（不含修饰符） |
| `method_body` | string | 方法完整源码 |
| `parameters` | array | 方法参数列表 |
| `return_type` | string | 返回值类型 |
| `parameter_class_info` | array | 参数中项目类的详细信息（可选） |
| `return_class_info` | object | 返回值类型的详细信息（可选，仅当返回类型为项目类时） |
| `context_prompt` | string | 为大模型生成的结构化上下文文本 |

### class_info / parameter_class_info / return_class_info 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `class_name` | string | 类的简单名 |
| `fqn` | string | 类的完全限定名 |
| `fields` | array | 类的所有字段 |
| `methods` | array | 类的所有方法（包含构造函数） |

### fields 数组元素结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 字段名 |
| `type` | string | 字段类型（解析后的 FQN 或原始类型） |
| `modifiers` | array | 修饰符列表（如 `public`, `static`, `final`） |
| `annotations` | array | 注解列表 |
| `raw_text` | string | 字段声明的完整源码 |
| `value` | string | 字段初始值（`=` 后的部分，可能为 null） |

### methods 数组元素结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 方法名 |
| `signature` | string | 完整签名（含修饰符、注解、返回类型） |
| `return_type` | string | 返回类型（构造函数为 null） |
| `modifiers` | array | 修饰符列表 |
| `annotations` | array | 注解列表 |
| `parameters` | array | 参数列表 |
| `raw_text` | string | 方法完整源码 |

## context_prompt 格式

`context_prompt` 是一个结构化的文本字段，用于帮助大模型理解待测函数的上下文：

```
// This is the context of method under test
Method Signature: multiply(Split)
Return Type: Split
Method Body:
public Split multiply(final Split b) {
    ...
}

// This is the context of class under test
Class Name: Split
Full Qualified Name: org.apache.commons.math4.core.jdkmath.AccurateMath.Split
Fields:
  private final double high;
  private final double low;
  ...
Constructors:
  Split(double)
  Split(double,double)
  Split(double,double,double)
Other Methods:
  public Split multiply(Split)
  public Split reciprocal()
  private Split pow(long)

// This is the context of return type class
Class Name: Split
...

// This is the context of parameter 'b' class
Class Name: Split
...
```

### context_prompt 包含的信息

1. **待测方法信息**：方法签名、返回类型、完整方法体
2. **待测类信息**：类名、FQN、所有字段、构造函数、其他方法
3. **返回值类信息**（如果返回类型是项目类）
4. **参数类信息**（如果参数类型是项目类）

## 注意事项

1. **method_key 中的参数类型**：使用简单类名即可，如 `Split` 而非完整 FQN
2. **内部类支持**：支持分析内部类的方法，FQN 格式为 `外部类.内部类`
3. **递归防护**：当参数类或返回类与待测类相同时，会标记 `recursion: true` 避免无限递归
4. **类型解析**：优先使用解析后的 FQN，如果无法解析则使用原始类型字符串

## 常见问题

### Q: 找不到方法？

检查 method_key 格式是否正确。可以先运行 `parser_main.py` 查看项目中所有已注册的方法签名。

### Q: 参数类/返回类信息为空？

只有当参数或返回类型是**项目内定义的类**时，才会输出对应的类信息。JDK 类或第三方库类不会被解析。

### Q: 如何查看所有可用的方法签名？

```bash
python parser_main.py /path/to/project /path/to/main /path/to/test
```

查看输出日志中的类和方法信息。

