Coloring by CSS
- The generator now emits SVGs whose modules use currentColor; each injected SVG receives class `qr-svg` and a `data-qr-default-foreground-color` attribute containing the default color. To change QR color via CSS, add a rule such as:

```css
.qr-svg { color: #b71c1c; } /* makes the QR modules red */
```

This would also include the ability for transparent QR codes.

That would look like this:

1. CSS Color is assigned to the QR SVG DIV. Which would make it that color via CSS.
2. The QR code being generated would have a transparent background and would be inverted of it's normal blocks.
3. That way the color from behind the image would shine through as the background color and the foreground color would be the only trhing rendered.

thus creating a see thru QR code, using less data and allowing the color to be changed by CSS instantly and without re-rendering.