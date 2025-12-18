#!/usr/bin/env python3
"""
Solution for preprocessing test combinations.

This script processes configuration files with compact bracket notation
and expands them into flat configurations.
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple, Set
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class ConfigurationProcessor:
    """Processes configuration strings with bracket notation."""
    
    def __init__(self):
        self.compact_configs = []
        self.flat_configs = []
    
    def parse_file(self, file_path: str) -> List[str]:
        """Parse input file and return list of configuration strings."""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        configs = []
        current_config = []
        
        for line in lines:
            line = line.rstrip()
            
            # Skip empty lines and comments
            if not line or line.strip().startswith('#'):
                # If we have a current config, end it
                if current_config:
                    config_str = ' '.join(current_config)
                    if config_str.strip():  # Only add non-empty configs
                        configs.append(config_str)
                    current_config = []
                continue
            
            # Remove leading/trailing whitespace
            line = line.strip()
            
            # Check if line ends with continuation
            if line.endswith('\\'):
                line = line[:-1].strip()
                current_config.append(line)
            else:
                current_config.append(line)
                # This ends a configuration
                config_str = ' '.join(current_config)
                if config_str.strip():  # Only add non-empty configs
                    configs.append(config_str)
                current_config = []
        
        # Handle any remaining config
        if current_config:
            config_str = ' '.join(current_config)
            if config_str.strip():  # Only add non-empty configs
                configs.append(config_str)
        
        return configs
    
    def normalize_whitespace(self, config: str) -> str:
        """Normalize whitespace in configuration."""
        return ' '.join(config.split())
    
    def find_innermost_brackets(self, config: str) -> Tuple[int, int]:
        """Find the innermost pair of square brackets."""
        stack = []
        innermost_start = -1
        innermost_end = -1
        max_depth = -1
        
        for i, char in enumerate(config):
            if char == '[':
                stack.append(i)
                if len(stack) > max_depth:
                    max_depth = len(stack)
                    innermost_start = i
            elif char == ']':
                if stack:
                    start = stack.pop()
                    if len(stack) + 1 == max_depth:
                        innermost_end = i
                        innermost_start = start
        
        if innermost_start != -1 and innermost_end != -1:
            return innermost_start, innermost_end
        return -1, -1
    
    def extract_bracket_elements(self, content: str) -> List[str]:
        """Extract elements from bracket content, treating {...} as single tokens."""
        elements = []
        i = 0
        n = len(content)
        
        while i < n:
            if content[i].isspace():
                i += 1
                continue
            
            if content[i] == '{':
                # Find matching brace
                brace_count = 1
                j = i + 1
                while j < n and brace_count > 0:
                    if content[j] == '{':
                        brace_count += 1
                    elif content[j] == '}':
                        brace_count -= 1
                    j += 1
                
                if brace_count == 0:
                    elements.append(content[i:j])
                    i = j
                else:
                    # Malformed braces, treat as regular character
                    elements.append(content[i])
                    i += 1
            else:
                # Regular token
                j = i
                while j < n and not content[j].isspace() and content[j] != '{':
                    j += 1
                elements.append(content[i:j])
                i = j
        
        return [elem.strip() for elem in elements if elem.strip()]
    
    def expand_brackets(self, config: str) -> List[str]:
        """Expand the innermost square brackets in configuration."""
        start, end = self.find_innermost_brackets(config)
        
        if start == -1:
            # No brackets to expand, remove curly braces if any
            return [self.remove_curly_braces(config)]
        
        # Extract content inside brackets
        bracket_content = config[start + 1:end]
        elements = self.extract_bracket_elements(bracket_content)
        
        if not elements:
            return [self.remove_curly_braces(config[:start] + config[end + 1:])]
        
        # Generate combinations
        results = []
        prefix = config[:start]
        suffix = config[end + 1:]
        
        for element in elements:
            # Remove curly braces from element
            clean_element = self.remove_curly_braces(element)
            new_config = prefix + clean_element + suffix
            results.append(new_config)
        
        return results
    
    def remove_curly_braces(self, config: str) -> str:
        """Remove curly braces from configuration."""
        result = []
        i = 0
        n = len(config)
        
        while i < n:
            if config[i] == '{':
                # Skip to matching brace
                brace_count = 1
                i += 1
                while i < n and brace_count > 0:
                    if config[i] == '{':
                        brace_count += 1
                    elif config[i] == '}':
                        brace_count -= 1
                    if brace_count > 0:
                        result.append(config[i])
                    i += 1
            else:
                result.append(config[i])
                i += 1
        
        return ''.join(result)
    
    def merge_duplicate_parameters(self, config: str) -> str:
        """Merge duplicate parameters by concatenating their properties."""
        # Split into tokens
        tokens = config.split()
        param_dict = {}
        
        for token in tokens:
            if '@' in token:
                param_part, prop_part = token.split('@', 1)
                
                if param_part not in param_dict:
                    param_dict[param_part] = []
                
                if prop_part:
                    # Split properties by comma and add to list
                    props = [p.strip() for p in prop_part.split(',') if p.strip()]
                    param_dict[param_part].extend(props)
                else:
                    # Empty properties are valid
                    pass
            else:
                # Handle edge case of token without @
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
        
        return ' '.join(result_tokens)
    
    def process_single_config(self, config: str) -> List[str]:
        """Process a single configuration through all expansions."""
        normalized = self.normalize_whitespace(config)
        if not normalized:
            return []
        
        pending = [normalized]
        completed = []
        seen = set()  # Only deduplicate within the same input configuration
        
        while pending:
            current = pending.pop(0)
            
            # Skip if we've already processed this exact configuration in this branch
            if current in seen:
                continue
            seen.add(current)
            
            # Try to expand brackets
            expanded = self.expand_brackets(current)
            
            if len(expanded) == 1 and expanded[0] == current:
                # No expansion possible, this configuration is complete
                merged = self.merge_duplicate_parameters(expanded[0])
                completed.append(merged)
            else:
                # Add expanded configurations back to pending
                for config in expanded:
                    normalized = self.normalize_whitespace(config)
                    if normalized:
                        pending.append(normalized)
        
        return completed
    
    def process_configurations(self, configs: List[str]) -> List[str]:
        """Process all configurations through expansion and merging."""
        all_completed = []
        
        for config in configs:
            completed = self.process_single_config(config)
            all_completed.extend(completed)
        
        return all_completed
    
    def sort_configurations(self, configs: List[str]) -> List[str]:
        """Sort configurations alphabetically."""
        return sorted(configs)
    
    def process_file(self, file_path: str) -> List[str]:
        """Process the entire file and return sorted configurations."""
        configs = self.parse_file(file_path)
        processed = self.process_configurations(configs)
        sorted_configs = self.sort_configurations(processed)
        return sorted_configs


def main():
    """Main function to process the input file."""
    if len(sys.argv) != 2:
        print("Usage: python solution.py <input_file>", file=sys.stderr)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        processor = ConfigurationProcessor()
        results = processor.process_file(file_path)
        
        for result in results:
            print(result)
    
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
