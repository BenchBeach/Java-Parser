# Java-Parser

Java项目静态解析器，用于提取方法信息、计算复杂度指标，支持单元测试难度评估。

## 📁 项目结构

```
Java-Parser/
├── core/                   # 核心数据结构
│   ├── clazz.py           # 类信息
│   ├── method.py          # 方法信息
│   ├── file.py            # 文件信息
│   ├── package.py         # 包信息
│   ├── project.py         # 项目上下文
│   ├── symbol_table.py    # 符号表
│   ├── types.py           # 类型信息
│   └── variables.py       # 变量信息
│
├── parser/                 # 解析器实现
│   ├── project_parser.py  # 项目解析器
│   ├── file_parser.py     # 文件解析器
│   ├── class_parser.py    # 类解析器
│   ├── method_parser.py   # 方法解析器
│   ├── field_parser.py    # 字段解析器
│   ├── type_parser.py     # 类型解析器
│   ├── body_parser.py     # 方法体解析器
│   └── utils.py           # 工具函数
│
├── metrics/                # 指标计算
│   ├── complexity_calculator.py  # 复杂度计算
│   ├── input_metrics.py          # 输入复杂度指标
│   ├── output_metrics.py         # 输出复杂度指标
│   └── aggregator.py             # 指标聚合
│
├── filters/                # 方法过滤器
│   ├── method_filter.py          # 基础过滤器
│   ├── config_filter.py          # 配置文件过滤器
│   └── test_coverage_filter.py   # 测试覆盖率过滤器
│
├── configs/                # 配置管理
│   └── config.py          # 配置加载
│
├── scripts/                # 辅助脚本
│   ├── README.md          # 脚本说明文档
│   └── get_all_content.py # 批量提取方法内容
│
├── tmp/                    # 临时数据（不提交到git）
│   ├── *.pkl              # 项目解析缓存
│   ├── *_metrics.json     # 指标数据
│   └── difficulty_analysis/  # 实验数据
│
├── parser_main.py          # 主解析入口
├── get_context.py          # 方法上下文提取
├── calculate_difficulty.py # 难度指标计算
├── select_methods.py       # 方法筛选
└── filter_config.yaml      # 过滤器配置文件
```

## 🔧 核心脚本

### parser_main.py
项目解析主入口，负责解析Java项目并生成符号表。

**功能**:
- 解析Java项目的main和test代码
- 构建完整的符号表
- 支持序列化保存/加载解析结果

**使用**:
```bash
python parser_main.py <project_root> <main_src> <test_src> --save output.pkl
```

### get_context.py
提取指定方法的完整上下文信息，用于单元测试生成。

**功能**:
- 提取方法签名、方法体
- 提取所属类的字段和方法
- 递归提取参数类型和返回值类型的类信息

**使用**:
```bash
python get_context.py <project_root> <main_src> <test_src> <method_key> --output context.json
```

### calculate_difficulty.py
计算方法的单元测试难度指标。

**功能**:
- 计算函数内部复杂度（圈复杂度、分支数等）
- 计算上下文依赖复杂度
- 计算输入/输出构造复杂度
- 聚合生成总体难度分数

**使用**:
```bash
python calculate_difficulty.py <project_root> <main_src> <test_src> --output metrics.json
# 或从已解析项目加载
python calculate_difficulty.py --load project.pkl --output metrics.json
```

### select_methods.py
基于配置文件筛选符合条件的方法。

**功能**:
- 根据YAML配置文件过滤方法
- 支持多种过滤条件（修饰符、注解、复杂度、测试覆盖率等）
- 输出筛选后的方法列表

**使用**:
```bash
python select_methods.py --load project.pkl --config filter_config.yaml --output selected.json
```

## 🎯 典型工作流

### 1. 解析项目
```bash
python parser_main.py /path/to/project src/main/java src/test/java --save tmp/project.pkl
```

### 2. 计算难度指标
```bash
python calculate_difficulty.py --load tmp/project.pkl --output tmp/metrics.json
```

### 3. 筛选方法
```bash
python select_methods.py --load tmp/project.pkl --config filter_config.yaml --output tmp/selected.json
```

### 4. 提取方法上下文
```bash
python get_context.py /path/to/project src/main/java src/test/java "com.example.MyClass#myMethod()" --load tmp/project.pkl --output tmp/context.json
```

## 📊 难度指标体系

### 输入复杂度 (60%)
- **函数内部复杂度**: 圈复杂度、分支数、循环数、异常路径
- **上下文依赖**: 字段依赖、外部调用、静态依赖
- **跨文件模块**: 依赖类数量、跨包调用
- **输入构造**: 参数类型复杂度、对象嵌套深度

### 输出复杂度 (40%)
- **测试结构**: Mock需求度、Setup复杂度
- **可观测性**: 返回值类型复杂度、副作用数量
- **断言构造**: 断言复杂度

### 难度等级
- **Easy**: 0.0 - 0.33
- **Medium**: 0.33 - 0.67
- **Hard**: 0.67 - 1.0

## 🔍 方法过滤器

支持通过YAML配置文件定义过滤规则：

```yaml
filters:
  modifiers:
    include: [public, protected]
    exclude: [abstract]

  annotations:
    exclude: [Deprecated, Generated]

  complexity:
    min_cyclomatic: 2
    max_cyclomatic: 20

  test_coverage:
    require_tests: true
    min_test_count: 1

  method_name:
    exclude_patterns:
      - "^get.*"
      - "^set.*"
      - "^is.*"
```

## 📝 更新日志

### 2024-04-08 - 项目清理
**删除的冗余脚本**:
- `compare_results.py` / `compare_by_method.py` - 临时对比脚本
- `plot_distribution.py` / `plot_distribution_en.py` - 临时可视化
- `plot_complexity_dist.py` - 临时可视化
- `analyze_difficulty_distribution.py` - 临时分析
- `analyze_difficulty_coverage.py` - 临时分析
- `analyze_complexity.py` - 临时分析
- `test_coverage_analysis.py` / `test_with_coverage.py` - 临时验证

**优化**:
- 根目录保留4个核心脚本
- 可复用脚本移至 `scripts/` 目录
- 项目结构更清晰

## 🛠️ 依赖

- Python 3.8+
- tree-sitter
- tree-sitter-java
- loguru
- pyyaml
- numpy (用于指标计算)
- matplotlib (用于可视化，可选)

## 📄 License

MIT
