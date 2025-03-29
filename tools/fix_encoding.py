#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File encoding fixer
Convert files to UTF-8 encoding
"""
import os
import sys
from pathlib import Path

def fix_file_encoding(file_path: str) -> bool:
    """Fix file encoding to UTF-8
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read file content with different encodings
        content = None
        encodings = ['utf-8', 'utf-16', 'gbk', 'gb2312', 'gb18030']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    break
            except UnicodeDecodeError:
                continue
                
        if content is None:
            print(f"Failed to read file: {file_path}")
            return False
            
        # Write content back in UTF-8
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Successfully converted {file_path} to UTF-8")
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python fix_encoding.py <file_or_directory>")
        sys.exit(1)
        
    target = sys.argv[1]
    
    if os.path.isfile(target):
        fix_file_encoding(target)
    elif os.path.isdir(target):
        for root, _, files in os.walk(target):
            for file in files:
                if file.endswith(('.py', '.yaml', '.yml', '.json', '.txt')):
                    file_path = os.path.join(root, file)
                    fix_file_encoding(file_path)
    else:
        print(f"Invalid target: {target}")
        sys.exit(1)

if __name__ == "__main__":
    main() 