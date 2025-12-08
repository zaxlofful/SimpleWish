# Recipients Folder

This folder contains text files that define wish lists for different recipients. Each text file is automatically converted into an HTML page during deployment.

## File Format

Each line in a recipient text file should follow this format:

```
Item description URL
```

- **Item description**: The name and details of the gift item
- **URL**: The web link to the product (must start with `http://` or `https://`)

The last space-separated token on each line is treated as the URL, and everything before it is the item description.

## Example

File: `recipients/alice.txt`

```
Raspberry Pi 5 — 8GB RAM starter kit https://example.com/raspberry-pi
Python Crash Course (3rd Edition) https://example.com/python-book
Mechanical keyboard — Cherry MX Blue switches https://example.com/mechanical-keyboard
Fitness smartwatch — heart rate monitoring https://example.com/smart-watch
```

This will generate `alice.html` with:
- Title: "Alice's Christmas List"
- Heading: "Christmas List for Alice"
- Four gift items with links

## Special Features

- **Comments**: Lines starting with `#` are ignored
- **Empty lines**: Blank lines are skipped
- **Name formatting**: The filename (without `.txt`) becomes the recipient name
  - `alice.txt` → "Alice"
  - `bob-smith.txt` → "Bob Smith"
  - Multi-word names are supported with hyphens

## Customization

The generated HTML files use the `index.html` template. If you want to customize colors or styling for a specific recipient, you can:

1. Let the CI generate the HTML file first
2. Manually edit the generated HTML file to add custom meta tags (for QR colors) or CSS variables
3. Commit the changes - the CI will preserve manual edits and only update the gift list items

## How It Works

1. Add or edit `.txt` files in this folder
2. Commit and push to GitHub
3. The GitHub Actions workflow automatically:
   - Generates HTML files from the text files
   - Creates QR codes for each HTML page
   - Deploys to GitHub Pages or Cloudflare Pages

## Notes

- Keep URLs clean (remove tracking parameters like `?utm_source=...`)
- Use proper URL encoding if needed
- Each text file should contain at least one valid item
