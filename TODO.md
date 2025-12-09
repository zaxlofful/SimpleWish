- Coloring by CSS

The generator now emits SVGs whose modules use qr-foreground-color; each injected SVG gets the HTML class `qrcode-box` applied to it.

This would also include the ability for transparent QR codes.

That would look like this:

- CSS Color is assigned to the QR SVG DIV. Which would make it that color via CSS.
- The QR code being generated would have a transparent background and would be inverted of it's normal blocks.
- That way the color from behind the image would shine through as the background color and the foreground color would be the only trhing rendered.

Thus creating a see thru QR code, using less data and allowing the color to be changed by CSS instantly and without re-rendering.