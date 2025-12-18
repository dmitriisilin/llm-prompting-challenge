#!/usr/bin/env python3
import glob
import os
import subprocess
import sys
from pathlib import Path

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"

def _normalize_configurations(config_lines):
    """Normalize configuration lines by sorting parameters and properties for comparison."""
    normalized = []
    for line in config_lines:
        # Split into tokens (parameters)
        tokens = line.split()
        if not tokens:
            continue
        
        # Group by parameter name
        param_groups = {}
        for token in tokens:
            if '@' in token:
                parts = token.split('@', 1)
                param_name = parts[0]
                properties = parts[1] if len(parts) > 1 else ""
                
                if param_name not in param_groups:
                    param_groups[param_name] = []
                
                # Split properties by comma and sort them
                if properties:
                    props = [p.strip() for p in properties.split(',') if p.strip()]
                    props.sort()  # Sort properties alphabetically
                    param_groups[param_name].extend(props)
            else:
                # Handle tokens without @ (edge case)
                if token not in param_groups:
                    param_groups[token] = []
        
        # Rebuild configuration with sorted parameters and properties
        sorted_params = sorted(param_groups.keys())
        result_tokens = []
        for param_name in sorted_params:
            properties = param_groups[param_name]
            if properties:
                # Remove duplicates while preserving sorted order
                seen = set()
                unique_props = []
                for prop in properties:
                    if prop not in seen:
                        seen.add(prop)
                        unique_props.append(prop)
                result_tokens.append(f"{param_name}@{','.join(unique_props)}")
            else:
                result_tokens.append(f"{param_name}@")
        
        normalized.append(' '.join(result_tokens))
    
    return normalized

def run_test(python_file, test_input, expected_output):
    try:
        result = subprocess.run(
            [sys.executable, python_file, str(Path(test_input).resolve())],
            text=True,
            capture_output=True,
            timeout=120
        )
        if result.returncode != 0:
            return False, f"failed with code: {result.returncode}: {result.stderr}"
        
        # Get actual output and split into lines
        actual_raw = result.stdout.rstrip('\n')
        actual_lines = [line.strip() for line in actual_raw.split('\n') if line.strip()]
        actual_sorted = sorted(_normalize_configurations(actual_lines))
        actual = '\n'.join(actual_sorted)
        
        # Get expected output and split into lines  
        with open(expected_output, 'r') as f:
            expected_raw = f.read().rstrip('\n')
        expected_lines = [line.strip() for line in expected_raw.split('\n') if line.strip()]
        expected_sorted = sorted(_normalize_configurations(expected_lines))
        expected = '\n'.join(expected_sorted)
        
        if actual == expected:
            return True, "OK"
        else:
            return False, f"{YELLOW}    expected (sorted):{RESET}\n{expected}\n{YELLOW}    actual (sorted):{RESET}\n{actual}"
    except subprocess.TimeoutExpired:
        return False, "timout (120 seconds)"
    except FileNotFoundError:
        return False, f"not found: {python_file}"
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    if len(sys.argv) != 3:
        print("usage: ./runner.py <python_file> <tests_directory>")
        sys.exit(1)
    python_file = sys.argv[1]
    tests_dir = sys.argv[2]
    if not os.path.exists(python_file):
        print(f"error: file '{python_file}' not found")
        sys.exit(1)
    if not os.path.exists(tests_dir):
        print(f"error: directori '{tests_dir}' not found")
        sys.exit(1)
    test_files = sorted(glob.glob(os.path.join(tests_dir, "test_*.in")))
    if not test_files:
        print(f"error: not found test files in directory '{tests_dir}'")
        sys.exit(1)
    print(f"running tests for: {python_file} ...")
    print("-" * 42)
    passed = 0
    failed = 0
    for test_input in test_files:
        test_name = os.path.basename(test_input).replace('.in', '')
        expected_output = test_input.replace('.in', '.out')
        if not os.path.exists(expected_output):
            print(f"{test_name}: skipped - {expected_output} not found")
            continue
        print(f"{test_name}: ", end="", flush=True)
        success, message = run_test(python_file, test_input, expected_output)
        if success:
            print(f"{GREEN}[PASS  ]{RESET}")
            passed += 1
        else:
            print(f"{RED}[  FAIL]{RESET}")
            print(f"{message}")
            failed += 1
    print("-" * 42)
    print(f"Results: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
