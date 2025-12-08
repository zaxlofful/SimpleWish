#!/usr/bin/env python3
"""Tests for generate_html_from_recipients.py script."""
import os
import sys
import tempfile
import unittest

# Import the functions we want to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from generate_html_from_recipients import (  # noqa: E402
    parse_recipient_file,
    generate_html_from_template,
)


class TestParseRecipientFile(unittest.TestCase):
    """Test the parse_recipient_file function."""

    def test_basic_parsing(self):
        """Test basic file parsing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Item 1 https://example.com/item1\n')
            f.write('Item 2 with details https://example.com/item2\n')
            f.name_for_test = f.name
        
        try:
            name, items = parse_recipient_file(f.name_for_test)
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0], ('Item 1', 'https://example.com/item1'))
            self.assertEqual(items[1], ('Item 2 with details', 'https://example.com/item2'))
        finally:
            os.unlink(f.name_for_test)

    def test_name_extraction(self):
        """Test recipient name extraction from filename."""
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.txt', delete=False,
                prefix='bob-smith-') as f:
            f.write('Item 1 https://example.com/item1\n')
            f.name_for_test = f.name
        
        try:
            name, items = parse_recipient_file(f.name_for_test)
            # Name should be capitalized
            self.assertTrue('Bob' in name or 'Smith' in name)
        finally:
            os.unlink(f.name_for_test)

    def test_skip_comments_and_empty_lines(self):
        """Test that comments and empty lines are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('# This is a comment\n')
            f.write('\n')
            f.write('Item 1 https://example.com/item1\n')
            f.write('  \n')
            f.write('# Another comment\n')
            f.write('Item 2 https://example.com/item2\n')
            f.name_for_test = f.name
        
        try:
            name, items = parse_recipient_file(f.name_for_test)
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0][0], 'Item 1')
            self.assertEqual(items[1][0], 'Item 2')
        finally:
            os.unlink(f.name_for_test)

    def test_url_validation(self):
        """Test URL validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Valid item https://example.com/item1\n')
            f.write('Invalid item not-a-url\n')
            f.write('Another valid http://example.com/item2\n')
            f.name_for_test = f.name
        
        try:
            name, items = parse_recipient_file(f.name_for_test)
            # Only valid URLs should be included
            self.assertEqual(len(items), 2)
            self.assertTrue(items[0][1].startswith('http'))
            self.assertTrue(items[1][1].startswith('http'))
        finally:
            os.unlink(f.name_for_test)


class TestGenerateHtmlFromTemplate(unittest.TestCase):
    """Test the generate_html_from_template function."""

    def setUp(self):
        """Set up a minimal template for testing."""
        self.template_content = '''<!doctype html>
<html>
<head>
<title>Christmas List Template</title>
</head>
<body>
<h1 id="recipient">Christmas List for [Recipient Name]</h1>
<ul id="gift-list" class="gift-list">
  <li><a href="https://example.com/old" target="_blank" rel="noopener">Old item</a></li>
</ul>
</body>
</html>'''

    def test_title_replacement(self):
        """Test that the title is correctly replaced."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(self.template_content)
            f.name_for_test = f.name
        
        try:
            items = [('Item 1', 'https://example.com/item1')]
            html = generate_html_from_template(f.name_for_test, 'Alice', items)
            self.assertIn("<title>Alice's Christmas List</title>", html)
        finally:
            os.unlink(f.name_for_test)

    def test_heading_replacement(self):
        """Test that the h1 heading is correctly replaced."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(self.template_content)
            f.name_for_test = f.name
        
        try:
            items = [('Item 1', 'https://example.com/item1')]
            html = generate_html_from_template(f.name_for_test, 'Bob', items)
            self.assertIn('<h1 id="recipient">Christmas List for Bob</h1>', html)
        finally:
            os.unlink(f.name_for_test)

    def test_gift_list_replacement(self):
        """Test that the gift list is correctly replaced."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(self.template_content)
            f.name_for_test = f.name
        
        try:
            items = [
                ('Item 1', 'https://example.com/item1'),
                ('Item 2', 'https://example.com/item2'),
            ]
            html = generate_html_from_template(f.name_for_test, 'Charlie', items)
            
            # Check that new items are present
            self.assertIn('Item 1', html)
            self.assertIn('Item 2', html)
            self.assertIn('https://example.com/item1', html)
            self.assertIn('https://example.com/item2', html)
            
            # Check that old item is not present
            self.assertNotIn('Old item', html)
        finally:
            os.unlink(f.name_for_test)

    def test_html_entity_escaping(self):
        """Test that HTML entities are properly escaped in descriptions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(self.template_content)
            f.name_for_test = f.name

        try:
            items = [('Item with & ampersand < less > greater', 'https://example.com/item1')]
            html = generate_html_from_template(f.name_for_test, 'Test', items)

            # Check that entities are escaped
            self.assertIn('&amp;', html)
            self.assertIn('&lt;', html)
            self.assertIn('&gt;', html)
        finally:
            os.unlink(f.name_for_test)

    def test_url_escaping(self):
        """Test that URLs with special characters are properly escaped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(self.template_content)
            f.name_for_test = f.name

        try:
            # URL with query parameters that contain special chars
            items = [('Test item', 'https://example.com/item?param="value"&other=<test>')]
            html = generate_html_from_template(f.name_for_test, 'Test', items)

            # Check that quotes and angle brackets in URL are escaped
            self.assertIn('&quot;', html)
            self.assertIn('&lt;', html)
            self.assertIn('&gt;', html)
            # Ensure the URL is in an href attribute
            self.assertIn('href=', html)
        finally:
            os.unlink(f.name_for_test)

    def test_recipient_name_escaping(self):
        """Test that recipient names with special characters are escaped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(self.template_content)
            f.name_for_test = f.name

        try:
            items = [('Item 1', 'https://example.com/item1')]
            html = generate_html_from_template(f.name_for_test, 'Bob & Alice', items)

            # Check that ampersand in name is escaped
            self.assertIn('Bob &amp; Alice', html)
            # Check both in title and heading
            self.assertIn("<title>Bob &amp; Alice's Christmas List</title>", html)
            self.assertIn('Christmas List for Bob &amp; Alice', html)
        finally:
            os.unlink(f.name_for_test)


if __name__ == '__main__':
    unittest.main()
