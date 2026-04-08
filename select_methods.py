#!/usr/bin/env python3
import argparse
import pickle
import json
from pathlib import Path
from filters.config_filter import ConfigFilter


def load_project(pickle_path: str):
    """Load project from pickle file"""
    with open(pickle_path, 'rb') as f:
        return pickle.load(f)


def collect_methods(project):
    """Collect all methods from project"""
    methods = []
    for cls in project.classes:
        for method in cls.methods:
            methods.append(method)
    return methods


def method_to_dict(method):
    """Convert method object to dictionary"""
    return {
        'package_name': method.package_name,
        'class_name': method.class_name,
        'method_name': method.name,
        'signature': method.signature,
        'return_type': method.return_type,
        'parameters': method.parameters,
        'modifiers': method.modifiers,
        'annotations': method.annotations,
        'cyclomatic_complexity': getattr(method, 'cyclomatic_complexity', None),
        'body_span': method.body_span,
        'file_path': method.file_path
    }


def main():
    parser = argparse.ArgumentParser(description='Select and filter methods from parsed project')
    parser.add_argument('--load', required=True, help='Path to project pickle file')
    parser.add_argument('--config', required=True, help='Path to filter config YAML file')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    args = parser.parse_args()

    print(f"Loading project from {args.load}...")
    project = load_project(args.load)

    print("Collecting methods...")
    all_methods = collect_methods(project)
    print(f"Total methods found: {len(all_methods)}")

    print(f"Loading filter config from {args.config}...")
    config_filter = ConfigFilter(args.config)

    print("Applying filters...")
    filtered_methods = config_filter.filter_methods(all_methods)
    print(f"Methods after filtering: {len(filtered_methods)}")
    print(f"Filtered out: {len(all_methods) - len(filtered_methods)} methods")

    print(f"Writing results to {args.output}...")
    output_data = {
        'total_methods': len(all_methods),
        'selected_methods': len(filtered_methods),
        'filtered_count': len(all_methods) - len(filtered_methods),
        'methods': [method_to_dict(m) for m in filtered_methods]
    }

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print("Done!")


if __name__ == '__main__':
    main()
