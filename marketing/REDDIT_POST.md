# Reddit Post: SimpleWish - Open Source Christmas List Generator

## Suggested Subreddits:
- r/opensource
- r/selfhosted
- r/Python
- r/webdev
- r/programming
- r/devops
- r/homelab
- r/privacy

## Post Title (Choose Based on Subreddit):

**Option 1 (r/opensource, r/Python):**
`SimpleWish - Privacy-focused Christmas gift list generator with automated QR codes and CI/CD (Python + GitHub Actions)`

**Option 2 (r/selfhosted, r/homelab):**
`Built a self-hostable Christmas gift list generator with zero external dependencies`

**Option 3 (r/devops, r/programming):**
`Overengineered my holiday gift lists - Full CI/CD pipeline for static HTML pages [Python/Docker/GitHub Actions]`

**Option 4 (r/privacy, r/webdev):**
`Made a privacy-respecting gift list app: no tracking, no external calls, fully offline-capable`

---

## Post Body:

### Main Content:

Hey everyone! 👋

I built **SimpleWish** - a printable Christmas gift list generator that might be the most over-engineered holiday project you'll see this year (in a good way, I promise).

**🎁 What is it?**

A single-file HTML template that generates personalized gift lists with embedded QR codes. Share the link, print it as PDF, or send it however you want. No databases, no servers, no tracking.

**🔒 Why I built it:**

Every holiday gift list tool I found either:
- Required creating an account
- Tracked everything you viewed
- Had ads everywhere
- Required internet connection to work
- Couldn't be printed nicely

I wanted something I could share with family without worrying about privacy, ads, or their data being sold.

**✨ Cool features:**

- **Single-file design**: Each HTML page is completely self-contained (all CSS inline, QR codes embedded as SVG). Works offline forever.
- **Automated QR generation**: CI/CD pipeline generates QR codes with cute Christmas decorations (trees, snowmen, Santa, etc.)
- **Privacy-first**: No external API calls, no tracking, no CDNs. Everything runs locally or in your CI.
- **Customizable**: JSON-based recipient system. Create `elsa.json` → get `elsa.html` with custom colors and items
- **Print-optimized**: CSS designed for clean PDF exports
- **CI/CD ready**: Full GitHub Actions pipeline - push JSON, get deployed HTML with QR codes

**🛠️ Tech Stack:**

- **Frontend**: Pure HTML/CSS (no JS required, though a tiny bit for optional URL copying)
- **Backend**: Python 3.11 (QR generation with segno + custom SVG decorations)
- **CI/CD**: GitHub Actions (7 automated workflows)
- **Deployment**: Cloudflare Pages (primary) or GitHub Pages (optional) or self-host anywhere
- **Testing**: pytest with visual regression tests (SHA256 hash validation)
- **Security**: CodeQL scanning, Trivy for container vulnerabilities
- **Container**: Custom Docker image (~200MB, python:3.11-slim based)

**🚀 How it works:**

1. Fork the repo
2. Add JSON files to `recipients/` (one per person)
3. Push to GitHub
4. CI automatically:
   - Generates HTML from your JSON templates
   - Creates decorated QR codes
   - Injects QR SVGs into HTML
   - Deploys to Cloudflare Pages
5. Share links or print PDFs

**Example JSON:**
```json
{
  "name": "Elsa",
  "items": [
    "Mechanical Keyboard (Cherry MX Blue)",
    "Raspberry Pi 5",
    "Ethical hacking book"
  ],
  "theme_color": "#1565C0",
  "qr_decoration": "snowman"
}
```

**🔐 Privacy Features:**

- No Google Analytics or tracking pixels
- No external font CDNs (all inline)
- QR codes generated locally (never sent to a service)
- No form submissions or data collection
- Can run completely offline after first load
- Self-hostable (just copy HTML files to any web server)

**🎨 Customization:**

- 7 decoration types (tree, snowman, santa, gift, star, candy-cane, bell)
- Fancy/plain variants for trees (with ornaments or without)
- Custom color themes (CSS variables)
- Per-recipient QR colors
- Responsive design (works on mobile too)

**📦 Easy Deploy Options:**

1. **Cloudflare Pages** (recommended): Free, auto-build from GitHub, custom domain support
2. **GitHub Pages**: Built-in GitHub integration
3. **Self-hosted**: Just HTML files, serve with nginx/Apache/anything
4. **Local only**: Open in browser, no server needed

**🧪 Overengineered? Maybe:**

- Custom Docker CI image with SHA pinning
- Automated TODO → GitHub Issue → Copilot workflow
- Reference-based visual regression tests
- Multiple deployment pipelines
- Build artifact exclusion automation
- CodeQL security scanning
- Trivy vulnerability checks

**But also practical:**

- One command setup: `./setup.sh`
- One command build: `./setup.sh --build`
- Works without any of the fancy CI (just open HTML)
- Clear documentation
- Actual tests that catch real bugs

**🤝 Contribute:**

This is open source (CC BY-NC-SA 4.0). Want to help?
- Add new QR decorations
- Create new color themes
- Improve the documentation
- Add i18n support
- Write more tests
- Make it prettier

**Ideas I haven't implemented yet:**
- Dark mode toggle
- Export to ICS calendar with "buy gift" reminders
- Price tracking integration (while respecting privacy)
- Gift idea suggestions (local only, no API calls)
- Multiple list variations (budgets, priorities)

**🔗 Links:**

GitHub: https://github.com/zaxlofful/SimpleWish
Live Demo: [Your deployment URL]
Documentation: [README.md](https://github.com/zaxlofful/SimpleWish#readme)

**📜 License:**

CC BY-NC-SA 4.0 - Free for personal use, educational use, and modification. Commercial use requires permission.

---

**TL;DR**: Made a privacy-respecting, printable gift list generator with way too much automation. Single-file HTML, automated QR codes, zero tracking. Fork it, use it, improve it.

**Tech people will like:** The CI/CD pipeline and Docker image
**Privacy people will like:** No tracking, no external calls
**Normal people will like:** It just works and looks nice

Questions, suggestions, or "why did you build this?" welcome! 😄

---

## Suggested Comment Responses:

**"Why not just use Google Docs/Excel?"**
> Fair question! Google Docs doesn't generate QR codes automatically, isn't optimized for printing, and requires a Google account. This works completely offline and is privacy-focused - no Google tracking your gift ideas. Plus it's a fun way to practice DevOps on a small project.

**"This is overengineered"**
> 100% guilty! 😄 But it's a great learning project. I wanted to practice CI/CD, containerization, and security scanning on something simple. Plus, the CI is optional - you can just open the HTML files directly if you want.

**"Can I use this for [other list type]?"**
> Absolutely! While it's themed for Christmas, the template works for any list - birthdays, weddings, wishlists, shopping lists, etc. Just edit the text and colors.

**"Does this work on mobile?"**
> Yes! The CSS is responsive. The QR code stays in a good position on smaller screens, and you can still print to PDF from mobile browsers.

**"What about [feature X]?"**
> Love the idea! Feel free to open an issue or PR. The codebase is pretty simple - single HTML template + Python scripts. Contribution guide is in CONTRIBUTING.md.

**"Security concerns?"**
> Great question! The project uses CodeQL for static analysis, Trivy for container scanning, and proper HTML escaping. No eval(), no innerHTML, no external scripts. All dependencies are pinned. Open to security audits!

**"Can I remove the attribution?"**
> The license (CC BY-NC-SA 4.0) requires attribution, so please keep the footer link. But you can customize everything else!

---

## Posting Strategy:

### For r/opensource:
- Lead with the privacy and open-source angle
- Emphasize contribution opportunities
- Focus on the license and community aspects

### For r/selfhosted:
- Lead with deployment options
- Emphasize zero dependencies and offline capability
- Focus on privacy and control

### For r/Python:
- Lead with the technical implementation
- Share code snippets of interesting parts (QR generation, CI/CD)
- Focus on pytest and code quality

### For r/devops:
- Lead with the CI/CD pipeline
- Emphasize automation and infrastructure as code
- Focus on the Docker image and GitHub Actions

### For r/programming:
- Lead with the technical challenge
- Show interesting code patterns
- Focus on the architecture decisions

### Post Timing:
- Best times: 9am-11am EST on weekdays
- Monday/Wednesday tend to get good engagement
- Avoid Friday afternoons

### Engagement:
- Respond to comments within first 30-60 minutes
- Be humble about the "overengineered" aspect
- Ask for feedback and feature ideas
- Share specific technical details when people ask
- Cross-post to multiple relevant subreddits (wait 24 hours between cross-posts)

### Visual Assets:
Consider adding:
1. Screenshot of the rendered HTML
2. Screenshot of the QR code with decorations
3. Diagram of the CI/CD pipeline
4. Before/after comparison (with and without QR code)
5. GIF showing the customization process

---

## Alternative Title Options:

**Casual/Friendly:**
- "I overengineered my Christmas gift lists and you can too"
- "Made a gift list app that respects your privacy [Open Source]"
- "Built a CI/CD pipeline for static Christmas cards (yes, really)"

**Technical/Serious:**
- "SimpleWish: Privacy-focused gift list generator with automated CI/CD"
- "Self-hosted Christmas list app with zero dependencies"
- "Open source gift list generator - Python, Docker, GitHub Actions"

**Engaging/Click-worthy:**
- "Tired of privacy-invading wishlist apps? I built an alternative"
- "Christmas gift lists don't need to track you - here's my solution"
- "Show HN: Privacy-respecting gift list generator with pretty QR codes"

Choose based on the subreddit culture and what you want to emphasize!
