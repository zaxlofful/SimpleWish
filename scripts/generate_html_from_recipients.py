#!/usr/bin/env python3
"""
Generate HTML files from recipient text files.

Usage:
    python scripts/generate_html_from_recipients.py --recipients-dir recipients --template index.html --output-dir .

This script reads text files from the recipients directory and generates HTML files
based on the template. Each line in the text file should be in the format:
    Item name URL

The generated HTML files will have the same name as the text files (with .html extension).

Requires Python 3.9+
"""
import argparse
import glob
import html
import os
import re
from typing import Tuple, List


def parse_recipient_file(file_path: str) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Parse a recipient text file and return the recipient name and list of items.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Tuple of (recipient_name, list of (item_description, url) tuples)
    """
    # Extract recipient name from filename (without extension)
    recipient_name = os.path.splitext(os.path.basename(file_path))[0]
    # Capitalize first letter of each word
    recipient_name = ' '.join(word.capitalize() for word in recipient_name.split('-'))
    
    items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                # Skip empty lines and comments
                continue
            
            # Try to parse the line - find the last URL-like pattern
            # Format: "Item description URL"
            # URL is the last space-separated token that looks like a URL
            parts = line.rsplit(None, 1)  # Split from right, max 1 split
            if len(parts) != 2:
                print(f"Warning: Line {line_num} in {file_path} doesn't match format 'description URL': {line}")
                continue
            
            description, url = parts
            
            # Basic URL validation
            if not (url.startswith('http://') or url.startswith('https://')):
                print(f"Warning: Line {line_num} in {file_path} has invalid URL: {url}")
                continue
            
            items.append((description, url))
    
    return recipient_name, items


def generate_html_from_template(template_path: str, recipient_name: str, items: List[Tuple[str, str]]) -> str:
    """
    Generate HTML content from template and items.
    
    Args:
        template_path: Path to the template HTML file
        recipient_name: Name of the recipient
        items: List of (description, url) tuples
        
    Returns:
        Generated HTML content
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Escape recipient name for safe HTML insertion
    recipient_name_escaped = html.escape(recipient_name)

    # Replace the title
    template = re.sub(
        r'<title>[^<]*</title>',
        f'<title>{recipient_name_escaped}\'s Christmas List</title>',
        template,
        count=1
    )

    # Replace the h1 recipient name
    template = re.sub(
        r'<h1[^>]*id="recipient"[^>]*>[^<]*</h1>',
        f'<h1 id="recipient">Christmas List for {recipient_name_escaped}</h1>',
        template,
        count=1
    )

    # Generate the gift list HTML
    gift_list_html = []
    for description, url in items:
        # Escape HTML entities in description and URL
        description_escaped = html.escape(description, quote=True)
        url_escaped = html.escape(url, quote=True)
        gift_list_html.append(
            f'          <li><a href="{url_escaped}" target="_blank" rel="noopener">{description_escaped}</a></li>'
        )
    
    gift_list_str = '\n'.join(gift_list_html)
    
    # Replace the gift list
    # Find the <ul id="gift-list" class="gift-list"> ... </ul> block
    gift_list_pattern = r'(<ul[^>]*id="gift-list"[^>]*>).*?(</ul>)'
    replacement = rf'\1\n{gift_list_str}\n          \2'
    template = re.sub(gift_list_pattern, replacement, template, flags=re.DOTALL)
    
    return template


def main():
    parser = argparse.ArgumentParser(
        description='Generate HTML files from recipient text files'
    )
    parser.add_argument(
        '--recipients-dir',
        default='recipients',
        help='Directory containing recipient text files (default: recipients)'
    )
    parser.add_argument(
        '--template',
        default='index.html',
        help='Template HTML file to use (default: index.html)'
    )
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Output directory for generated HTML files (default: current directory)'
    )
    parser.add_argument(
        '--pattern',
        default='*.txt',
        help='Pattern for recipient files (default: *.txt)'
    )
    args = parser.parse_args()
    
    # Find all recipient text files
    pattern_path = os.path.join(args.recipients_dir, args.pattern)
    recipient_files = glob.glob(pattern_path)
    
    if not recipient_files:
        print(f'No recipient files found matching {pattern_path}')
        return 0
    
    # Check if template exists
    if not os.path.exists(args.template):
        print(f'Error: Template file not found: {args.template}')
        return 1
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    generated_count = 0
    for recipient_file in recipient_files:
        try:
            # Parse the recipient file
            recipient_name, items = parse_recipient_file(recipient_file)
            
            if not items:
                print(f'Warning: No valid items found in {recipient_file}, skipping')
                continue
            
            # Generate HTML from template
            html_content = generate_html_from_template(args.template, recipient_name, items)
            
            # Determine output filename
            base_name = os.path.splitext(os.path.basename(recipient_file))[0]
            output_path = os.path.join(args.output_dir, f'{base_name}.html')
            
            # Write the generated HTML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f'Generated {output_path} for {recipient_name} ({len(items)} items)')
            generated_count += 1
            
        except Exception as e:
            print(f'Error processing {recipient_file}: {e}')
            continue
    
    print(f'Successfully generated {generated_count} HTML file(s)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
