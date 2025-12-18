#!/usr/bin/env python3
"""
Solution for preprocessing test configurations.

This script expands compact test configuration representations into flat form.
It handles bracket notation [...] for Cartesian products and {...} for grouping.
"""

import sys
import re
from typing import List, Tuple, Set
import os

def debug_print(message: str):
    """Debug print function that can be easily removed later."""
    pass

def parse_file(filepath: str) -> List[str]:
    """Parse input file and return list of configurations."""
    debug_print(f"Parsing file: {filepath}")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    configurations = []
    current_config_tokens = []
    
    for line_num, line in enumerate(lines, 1):
        original_line = line.rstrip('\n')
        line_stripped = line.strip()
        
        debug_print(f"Line {line_num}: '{original_line}' -> stripped: '{line_stripped}'")
        
        # Skip empty lines and comments
        if not line_stripped or line_stripped.startswith('#'):
            debug_print(f"Skipping empty/comment line: {line_stripped}")
            if current_config_tokens:
                config_str = ' '.join(current_config_tokens)
                if config_str.strip():  # Only add non-empty configurations
                    debug_print(f"Adding configuration: {config_str}")
                    configurations.append(config_str)
                current_config_tokens = []
            continue
        
        # Process the line content
        line_content = line_stripped
        if line_content.endswith('\\'):
            # Remove the backslash continuation character
            line_content = line_content[:-1].strip()
        
        # Tokenize the line and add to current config
        if line_content:
            tokens = line_content.split()
            current_config_tokens.extend(tokens)
            debug_print(f"Added tokens: {tokens}, current_config_tokens: {current_config_tokens}")
        
        # If line doesn't end with \, this is the end of a configuration
        if not line_stripped.endswith('\\'):
            if current_config_tokens:
                config_str = ' '.join(current_config_tokens)
                if config_str.strip():  # Only add non-empty configurations
                    debug_print(f"Complete configuration: {config_str}")
                    configurations.append(config_str)
                current_config_tokens = []
    
    # Handle last configuration if file doesn't end with newline
    if current_config_tokens:
        config_str = ' '.join(current_config_tokens)
        if config_str.strip():  # Only add non-empty configurations
            debug_print(f"Adding final configuration: {config_str}")
            configurations.append(config_str)
    
    debug_print(f"Parsed {len(configurations)} configurations")
    for i, config in enumerate(configurations):
        debug_print(f"Config {i}: {config}")
    return configurations

def find_innermost_brackets(text: str) -> Tuple[int, int]:
    """Find the innermost [ ] brackets in the text."""
    debug_print(f"Finding innermost brackets in: {text}")
    
    max_depth = -1
    innermost_start = -1
    innermost_end = -1
    current_depth = 0
    stack = []
    
    for i, char in enumerate(text):
        if char == '[':
            stack.append(i)
            current_depth += 1
            debug_print(f"Found '[' at position {i}, depth: {current_depth}")
        elif char == ']':
            if stack:
                start_pos = stack.pop()
                current_depth -= 1
                debug_print(f"Found ']' at position {i}, depth: {current_depth}, matching start: {start_pos}")
                
                # Check if this is the deepest nested pair
                if current_depth + 1 > max_depth:
                    max_depth = current_depth + 1
                    innermost_start = start_pos
                    innermost_end = i
                    debug_print(f"New deepest brackets: [{innermost_start}, {innermost_end}] at depth {max_depth}")
    
    if innermost_start != -1 and innermost_end != -1:
        debug_print(f"Returning innermost brackets: [{innermost_start}, {innermost_end}] at depth {max_depth}")
        return innermost_start, innermost_end
    
    debug_print("No brackets found")
    return -1, -1

def extract_elements_from_brackets(content: str) -> List[str]:
    """Extract elements from brackets content, treating {...} as single elements."""
    debug_print(f"Extracting elements from: {content}")
    
    elements = []
    i = 0
    n = len(content)
    
    while i < n:
        if content[i].isspace():
            i += 1
            continue
        
        if content[i] == '{':
            # Find matching closing brace
            brace_count = 1
            j = i + 1
            while j < n and brace_count > 0:
                if content[j] == '{':
                    brace_count += 1
                elif content[j] == '}':
                    brace_count -= 1
                j += 1
            
            if brace_count == 0:
                element = content[i:j]
                elements.append(element)
                debug_print(f"Found brace element: {element}")
                i = j
            else:
                # Unmatched braces, treat as regular character
                i += 1
        else:
            # Regular token
            j = i
            while j < n and not content[j].isspace() and content[j] != '{':
                j += 1
            
            element = content[i:j]
            elements.append(element)
            debug_print(f"Found regular element: {element}")
            i = j
    
    debug_print(f"Extracted elements: {elements}")
    return elements

def expand_brackets(configuration: str) -> List[str]:
    """Expand the innermost brackets in a configuration."""
    debug_print(f"Expanding brackets in: {configuration}")
    
    start, end = find_innermost_brackets(configuration)
    
    if start == -1:
        debug_print("No brackets to expand")
        return [configuration]
    
    # Extract content inside brackets
    bracket_content = configuration[start + 1:end]
    debug_print(f"Bracket content: '{bracket_content}'")
    
    # Extract elements from brackets
    elements = extract_elements_from_brackets(bracket_content)
    
    if not elements:
        debug_print("No elements found in brackets")
        return [configuration]
    
    debug_print(f"Elements to expand: {elements}")
    
    # Create new configurations by replacing brackets with each element
    # Get the parts before and after the brackets, preserving spacing
    before_bracket = configuration[:start]
    after_bracket = configuration[end + 1:]
    
    # Clean up whitespace
    prefix = before_bracket.rstrip()
    suffix = after_bracket.lstrip()
    
    debug_print(f"Before bracket: '{before_bracket}', After bracket: '{after_bracket}'")
    debug_print(f"Prefix: '{prefix}', Suffix: '{suffix}'")
    
    new_configurations = []
    for element in elements:
        # Remove braces from element if present
        if element.startswith('{') and element.endswith('}'):
            element = element[1:-1].strip()
        else:
            element = element.strip()
        
        # Combine parts, handling spaces properly
        parts = []
        if prefix:
            parts.append(prefix)
        if element:
            parts.append(element)
        if suffix:
            parts.append(suffix)
        
        new_config = ' '.join(parts)
        new_configurations.append(new_config)
        debug_print(f"Created new configuration: '{new_config}'")
    
    debug_print(f"Expanded into {len(new_configurations)} configurations")
    return new_configurations

def remove_braces(text: str) -> str:
    """Remove all {...} braces from text."""
    debug_print(f"Removing braces from: {text}")
    
    result = []
    i = 0
    n = len(text)
    
    while i < n:
        if text[i] == '{':
            # Skip to matching closing brace
            brace_count = 1
            j = i + 1
            while j < n and brace_count > 0:
                if text[j] == '{':
                    brace_count += 1
                elif text[j] == '}':
                    brace_count -= 1
                j += 1
            
            # Extract content inside braces
            content = text[i + 1:j - 1]
            result.append(content)
            debug_print(f"Found brace content: {content}")
            i = j
        else:
            result.append(text[i])
            i += 1
    
    cleaned = ''.join(result)
    debug_print(f"Braces removed: {cleaned}")
    return cleaned

def merge_duplicate_parameters(configuration: str) -> str:
    """Merge duplicate parameters in a configuration."""
    debug_print(f"Merging duplicate parameters in: {configuration}")
    
    tokens = configuration.split()
    param_dict = {}
    
    for token in tokens:
        if '@' in token:
            param_name, properties = token.split('@', 1)
            if param_name not in param_dict:
                param_dict[param_name] = []
            
            # Split properties by comma and add to list
            if properties:
                props = [p.strip() for p in properties.split(',') if p.strip()]
                param_dict[param_name].extend(props)
        else:
            # Handle tokens without @ (edge case)
            if token not in param_dict:
                param_dict[token] = []
    
    # Rebuild configuration
    result_tokens = []
    for param_name, properties in param_dict.items():
        if properties:
            # Remove duplicates while preserving order
            seen = set()
            unique_props = []
            for prop in properties:
                if prop not in seen:
                    seen.add(prop)
                    unique_props.append(prop)
            
            result_tokens.append(f"{param_name}@{','.join(unique_props)}")
        else:
            result_tokens.append(f"{param_name}@")
    
    result = ' '.join(result_tokens)
    debug_print(f"Merged configuration: {result}")
    return result

def process_configurations(configurations: List[str]) -> List[str]:
    """Process all configurations until no brackets remain."""
    debug_print(f"Processing {len(configurations)} configurations")
    
    # Process each input configuration separately to preserve inter-configuration duplicates
    all_final_configs = []
    
    for input_config_idx, input_config in enumerate(configurations):
        debug_print(f"Processing input configuration {input_config_idx}: {input_config}")
        
        compact_configs = [input_config]
        flat_configs = []
        
        iteration = 0
        while compact_configs:
            iteration += 1
            debug_print(f"  Iteration {iteration}, compact configs: {len(compact_configs)}")
            
            new_compact_configs = []
            
            for config in compact_configs:
                debug_print(f"  Processing config: {config}")
                
                # Try to expand brackets
                expanded = expand_brackets(config)
                
                if len(expanded) == 1 and expanded[0] == config:
                    # No expansion possible, move to flat
                    debug_print(f"  No expansion possible, adding to flat: {config}")
                    flat_configs.append(config)
                else:
                    # Expansion happened, add to new compact
                    for new_config in expanded:
                        new_compact_configs.append(new_config)
                        debug_print(f"  Added to new compact: {new_config}")
            
            compact_configs = new_compact_configs
            debug_print(f"  After iteration {iteration}: {len(compact_configs)} compact, {len(flat_configs)} flat")
        
        # Remove braces and merge parameters in flat configurations
        final_configs_for_input = []
        for config in flat_configs:
            debug_print(f"  Final processing of: {config}")
            
            # Remove braces
            config_no_braces = remove_braces(config)
            
            # Merge duplicate parameters
            config_merged = merge_duplicate_parameters(config_no_braces)
            
            final_configs_for_input.append(config_merged)
            debug_print(f"  Final result: {config_merged}")
        
        # Remove duplicates that came from the same input configuration only
        seen_configs = set()
        unique_configs_for_input = []
        for config in final_configs_for_input:
            if config not in seen_configs:
                seen_configs.add(config)
                unique_configs_for_input.append(config)
                debug_print(f"  Kept unique config: {config}")
            else:
                debug_print(f"  Removed duplicate config from same input: {config}")
        
        all_final_configs.extend(unique_configs_for_input)
        debug_print(f"  Input {input_config_idx}: {len(final_configs_for_input)} -> {len(unique_configs_for_input)} unique")
    
    debug_print(f"Processed {len(configurations)} input configurations, {len(all_final_configs)} total final configs")
    return all_final_configs

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python solution.py <input_file>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    debug_print(f"Starting processing of file: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Parse configurations from file
    configurations = parse_file(input_file)
    
    # Process configurations
    processed_configs = process_configurations(configurations)
    
    # Sort and output results
    processed_configs.sort()
    for config in processed_configs:
        print(config)
    
    debug_print("Processing completed successfully")

if __name__ == "__main__":
    main()
