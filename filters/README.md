# Method Selection and Filtering System

## Overview
This system filters and selects methods from parsed Java projects to build high-quality benchmark datasets.

## Components

### Filters (`filters/`)
- `GetterSetterFilter`: Removes simple getter/setter methods
- `TestUtilityFilter`: Removes test utility methods (@Before, @After, setUp, etc.)
- `MetricBasedFilter`: Filters based on complexity, parameters, and code lines
- `SimilarityFilter`: Removes duplicate/similar method implementations

### Configuration (`filter_config.yaml`)
YAML file to configure which filters to enable and their thresholds.

### Main Script (`select_methods.py`)
Applies configured filters to parsed projects and outputs selected methods.

## Usage

```bash
# Parse a project first
python parser_main.py /path/to/project src/main/java src/test/java --save project.pkl

# Select methods using filters
python select_methods.py --load project.pkl --config filter_config.yaml --output selected_methods.json
```

## Configuration Example

```yaml
filters:
  getter_setter: true
  test_utility: true
  metric_based:
    enabled: true
    min_cyclomatic_complexity: 2
    max_cyclomatic_complexity: 50
  similarity:
    enabled: true
    threshold: 0.85

exclude_methods:
  - "toString"
  - "hashCode"
```

## Output Format

JSON file containing:
- `total_methods`: Original method count
- `selected_methods`: Filtered method count
- `filtered_count`: Number of methods removed
- `methods`: Array of selected method details
