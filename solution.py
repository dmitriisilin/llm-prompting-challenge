#!/usr/bin/env python3
"""
Configuration preprocessor for test combinations.

This script processes compact configuration descriptions and expands them
into flat configurations by resolving bracket notations and merging parameters.
"""

import sys
from typing import List, Set, Dict
from collections import OrderedDict


class ConfigurationProcessor:
    """Handles the processing of test configurations."""
    
    def __init__(self):
        self.compact_configs: List[str] = []
        self.flat_configs: List[str] = []
    
    def read_configurations(self, file_path: str) -> None:
        """Read and parse configurations from input file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")
        
        self._parse_configurations(lines)
    
    def _parse_configurations(self, lines: List[str]) -> None:
        """Parse lines into configurations."""
        current_config = []
        
        for line in lines:
            # Remove trailing newline but keep other whitespace
            line = line.rstrip('\n')
            stripped = line.strip()
            
            # Skip comments
            if stripped.startswith('#'):
                continue
            
            # Handle empty lines
            if not stripped:
                if current_config:
                    config_text = ' '.join(current_config).strip()
                    if config_text:
                        self.compact_configs.append(config_text)
                    current_config = []
                continue
            
            # Handle line continuation
            if line.endswith('\\'):
                content_part = stripped[:-1].strip()
                current_config.append(content_part)
            else:
                current_config.append(stripped)
                # Configuration ends here
                config_text = ' '.join(current_config).strip()
                if config_text:
                    self.compact_configs.append(config_text)
                current_config = []
        
        # Handle last configuration
        if current_config:
            config_text = ' '.join(current_config).strip()
            if config_text:
                self.compact_configs.append(config_text)
    
    def process_configurations(self) -> None:
        """Process all compact configurations into flat configurations."""
        # Process each original configuration separately to preserve duplicates only from input
        for original_config in self.compact_configs:
            self._process_single_config(original_config)
    
    def _process_single_config(self, original_config: str) -> None:
        """Process a single configuration and its expansions."""
        to_process = [original_config]
        processed = set()
        
        while to_process:
            config = to_process.pop(0)
            
            if config in processed:
                continue
                
            processed.add(config)
            
            expanded = self._expand_config(config)
            
            if len(expanded) == 0 or expanded == [config]:
                # No more expansion possible
                merged = self._merge_parameters(config)
                self.flat_configs.append(merged)
            else:
                # Add expanded configs back to process
                to_process.extend(expanded)
    
    def _expand_config(self, config: str) -> List[str]:
        """Expand configuration by finding and resolving most nested brackets."""
        # Find most nested square brackets
        bracket_pos = self._find_most_nested_square_brackets(config)
        
        if bracket_pos:
            start, end = bracket_pos
            content = config[start + 1:end]
            
            # Parse elements in brackets
            elements = self._parse_bracket_content(content)
            
            # Clean elements (remove curly braces)
            cleaned_elements = []
            for elem in elements:
                cleaned = self._remove_curly_braces(elem).strip()
                if cleaned:
                    cleaned_elements.append(cleaned)
            
            if len(cleaned_elements) <= 1:
                # Just remove brackets
                if cleaned_elements:
                    new_config = config[:start] + cleaned_elements[0] + config[end + 1:]
                else:
                    new_config = config[:start] + config[end + 1:]
                return [self._normalize_whitespace(new_config)]
            
            # Generate expansions
            result = []
            for elem in cleaned_elements:
                new_config = config[:start] + elem + config[end + 1:]
                result.append(self._normalize_whitespace(new_config))
            
            return result
        
        # Check for curly braces to remove
        if '{' in config and '}' in config:
            cleaned = self._remove_curly_braces(config)
            normalized = self._normalize_whitespace(cleaned)
            if normalized != config:
                return [normalized]
        
        return []  # No expansion possible
    
    def _find_most_nested_square_brackets(self, config: str) -> tuple:
        """Find the most nested square brackets."""
        max_depth = -1
        result = None
        stack = []
        
        for i, char in enumerate(config):
            if char == '[':
                stack.append(i)
            elif char == ']' and stack:
                start = stack.pop()
                depth = len(stack) + 1
                if depth > max_depth:
                    max_depth = depth
                    result = (start, i)
        
        return result
    
    def _parse_bracket_content(self, content: str) -> List[str]:
        """Parse content inside square brackets."""
        elements = []
        current = ""
        in_curly = 0
        
        for char in content:
            if char == '{':
                in_curly += 1
                current += char
            elif char == '}':
                in_curly -= 1
                current += char
            elif char == ' ' and in_curly == 0:
                if current.strip():
                    elements.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            elements.append(current.strip())
        
        return elements
    
    def _remove_curly_braces(self, s: str) -> str:
        """Remove curly braces from string."""
        result = []
        
        for char in s:
            if char != '{' and char != '}':
                result.append(char)
        
        return ''.join(result)
    
    def _normalize_whitespace(self, s: str) -> str:
        """Normalize whitespace."""
        return ' '.join(s.split())
    
    def _merge_parameters(self, config: str) -> str:
        """Merge duplicate parameters."""
        if not config.strip():
            return ""
        
        tokens = config.split()
        param_dict = OrderedDict()
        
        for token in tokens:
            if '@' in token:
                parts = token.split('@', 1)
                name = parts[0]
                props = parts[1] if len(parts) > 1 else ""
                
                if name not in param_dict:
                    param_dict[name] = []
                
                if props:
                    for prop in props.split(','):
                        prop = prop.strip()
                        if prop and prop not in param_dict[name]:
                            param_dict[name].append(prop)
            else:
                # Handle tokens without @
                if token not in param_dict:
                    param_dict[token] = []
        
        # Rebuild
        result = []
        for name, props in param_dict.items():
            if props:
                result.append(f"{name}@{','.join(props)}")
            else:
                result.append(f"{name}@")
        
        return ' '.join(result)
    
    def print_results(self) -> None:
        """Print the processed flat configurations."""
        for config in self.flat_configs:
            print(config)


def main():
    """Main function to process configurations."""
    if len(sys.argv) != 2:
        print("Usage: python solution.py <input_file>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        processor = ConfigurationProcessor()
        processor.read_configurations(input_file)
        processor.process_configurations()
        processor.print_results()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
