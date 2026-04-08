#!/usr/bin/env python3
import pickle
import json
import sys
from pathlib import Path

def main():
    pkl_path = Path(__file__).parent / "tmp" / "commons-lang.pkl"

    with open(pkl_path, 'rb') as f:
        project = pickle.load(f)

    symbol_table = project.symbols

    results = []
    for method_key, method in symbol_table.methods.items():
        class_fqn = method_key.split("#")[0]
        cls = symbol_table.get_class(class_fqn)

        if cls and method:
            from get_context import collect_method_context
            context = collect_method_context(method, cls, symbol_table)
            results.append({
                "method_key": method_key,
                "context": context
            })

    output_file = Path(__file__).parent / "tmp" / "commons-lang-all-content.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(results)} methods to {output_file}")

if __name__ == '__main__':
    main()
