use qrcode::{Color, EcLevel, QrCode};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

use crate::{matches_pattern, url_encode_path, MARKER_END, MARKER_START};

const DEFAULT_FOREGROUND: &str = "#0b6623";
const KNOWN_META: [&str; 5] = [
    "qr-foreground-color",
    "qr-background-color",
    "qr-decorate",
    "qr-tree-style",
    "qr-decoration-type",
];

#[derive(Clone)]
pub struct QrOptions {
    pub foreground: String,
    pub background: String,
    pub decorate: bool,
    pub logo_size: f64,
    pub overlay_multiplier: f64,
    pub overlay_shift_x: f64,
    pub overlay_shift_y: f64,
    pub ecc: EcLevel,
    pub tree_style: String,
    pub decoration_type: String,
}

impl Default for QrOptions {
    fn default() -> Self {
        Self {
            foreground: DEFAULT_FOREGROUND.to_string(),
            background: "#ffffff".to_string(),
            decorate: true,
            logo_size: 20.0,
            overlay_multiplier: 3.0,
            overlay_shift_x: 0.90,
            overlay_shift_y: 0.50,
            ecc: EcLevel::H,
            tree_style: "fancy".to_string(),
            decoration_type: "tree".to_string(),
        }
    }
}

pub fn read_meta_tags_from_html(path: &Path) -> HashMap<String, String> {
    let Ok(content) = fs::read_to_string(path) else {
        return HashMap::new();
    };
    let uncommented = remove_html_comments(&content);
    let mut tags = HashMap::new();
    let mut rest = uncommented.as_str();
    while let Some(start) = find_ascii_case_insensitive(rest, "<meta") {
        rest = &rest[start + 5..];
        let Some(end) = rest.find('>') else {
            break;
        };
        let attrs = parse_attributes(&rest[..end]);
        if let (Some(name), Some(value)) = (attrs.get("name"), attrs.get("content")) {
            let name = name.trim().to_ascii_lowercase();
            if KNOWN_META.contains(&name.as_str()) {
                tags.insert(name, value.trim().to_string());
            }
        }
        rest = &rest[end + 1..];
    }
    tags
}

fn remove_html_comments(content: &str) -> String {
    let mut output = String::with_capacity(content.len());
    let mut remaining = content;
    while let Some(start) = remaining.find("<!--") {
        output.push_str(&remaining[..start]);
        remaining = &remaining[start + 4..];
        let Some(end) = remaining.find("-->") else {
            return output;
        };
        remaining = &remaining[end + 3..];
    }
    output.push_str(remaining);
    output
}

fn find_ascii_case_insensitive(haystack: &str, needle: &str) -> Option<usize> {
    haystack
        .as_bytes()
        .windows(needle.len())
        .position(|window| window.eq_ignore_ascii_case(needle.as_bytes()))
}

fn parse_attributes(text: &str) -> HashMap<String, String> {
    let mut attributes = HashMap::new();
    let bytes = text.as_bytes();
    let mut cursor = 0;
    while cursor < bytes.len() {
        while cursor < bytes.len()
            && (bytes[cursor].is_ascii_whitespace() || bytes[cursor] == b'/')
        {
            cursor += 1;
        }
        let name_start = cursor;
        while cursor < bytes.len()
            && !bytes[cursor].is_ascii_whitespace()
            && bytes[cursor] != b'='
            && bytes[cursor] != b'/'
        {
            cursor += 1;
        }
        if name_start == cursor {
            cursor += 1;
            continue;
        }
        let name = text[name_start..cursor].to_ascii_lowercase();
        while cursor < bytes.len() && bytes[cursor].is_ascii_whitespace() {
            cursor += 1;
        }
        if cursor == bytes.len() || bytes[cursor] != b'=' {
            continue;
        }
        cursor += 1;
        while cursor < bytes.len() && bytes[cursor].is_ascii_whitespace() {
            cursor += 1;
        }
        if cursor == bytes.len() {
            break;
        }
        let quote = bytes[cursor];
        let value = if quote == b'\'' || quote == b'"' {
            cursor += 1;
            let value_start = cursor;
            while cursor < bytes.len() && bytes[cursor] != quote {
                cursor += 1;
            }
            let value = text[value_start..cursor].to_string();
            cursor += usize::from(cursor < bytes.len());
            value
        } else {
            let value_start = cursor;
            while cursor < bytes.len() && !bytes[cursor].is_ascii_whitespace() {
                cursor += 1;
            }
            text[value_start..cursor].to_string()
        };
        attributes.insert(name, value);
    }
    attributes
}

pub fn generate_svg(url: &str, options: &QrOptions) -> Result<String, String> {
    let code = QrCode::with_error_correction_level(url.as_bytes(), options.ecc)
        .map_err(|error| format!("cannot encode QR URL: {error}"))?;
    let width = code.width();
    let border = if options.decorate { 0 } else { 8 };
    let size = width + border * 2;
    let mut modules = String::new();
    for y in 0..width {
        for x in 0..width {
            if code[(x, y)] == Color::Dark {
                modules.push_str(&format!(
                    "M{} {}h1v1h-1z",
                    x + border,
                    y + border
                ));
            }
        }
    }
    let mut svg = format!(
        "<svg xmlns=\"http://www.w3.org/2000/svg\" class=\"qr-svg qrcode-box\" \
         data-qr-default-foreground-color=\"{}\" width=\"250\" height=\"250\" \
         viewBox=\"0 0 {size} {size}\">\n<path fill=\"currentColor\" d=\"{modules}\"/>\n",
        crate::html_escape(&options.foreground, true)
    );
    if options.decorate {
        let fragment = decoration(&options.decoration_type, &options.tree_style);
        let rect_size = size as f64 * options.logo_size / 100.0;
        let padding = size as f64 * 0.01;
        let desired_size = rect_size * options.overlay_multiplier;
        let mut x = size as f64 - rect_size - padding;
        let mut y = size as f64 - rect_size - padding;
        x += rect_size - desired_size + rect_size * options.overlay_shift_x;
        y += rect_size - desired_size + rect_size * options.overlay_shift_y;
        match options.decoration_type.as_str() {
            "bell" => {
                x += rect_size * 0.10;
                y += rect_size * 0.12;
            }
            "star" => {
                x += rect_size * 0.10;
                y += rect_size * 0.50;
            }
            "santa" => y += rect_size * 0.50,
            "snowman" => {
                x += rect_size * 0.06;
                y += rect_size * 0.45;
            }
            "gift" => x += rect_size * 0.05,
            _ => {}
        }
        svg.push_str(&format!(
            "<g id=\"xmas-decoration\" transform=\"translate({x:.2}, {y:.2}) scale({:.6})\" aria-hidden=\"true\">\n{fragment}\n</g>\n",
            desired_size / 200.0
        ));
    }
    svg.push_str("</svg>\n");
    Ok(svg)
}

fn decoration(decoration_type: &str, tree_style: &str) -> &'static str {
    match decoration_type {
        "tree" if tree_style == "plain" => TREE_PLAIN,
        "tree" => TREE_FANCY,
        "snowman" => SNOWMAN,
        "santa" => SANTA,
        "gift" => GIFT,
        "star" => STAR,
        "candy-cane" => CANDY_CANE,
        "bell" => BELL,
        _ => TREE_FANCY,
    }
}

const TREE_PLAIN: &str = r##"<g>
    <polygon points="50,185 100,115 150,185" fill="#0b6623" />
    <polygon points="60,155 100,95 140,155" fill="#0b6623" />
    <polygon points="70,130 100,70 130,130" fill="#0b6623" />
</g>"##;

const TREE_FANCY: &str = r##"<g>
    <polygon points="50,185 100,115 150,185" fill="#0b6623" />
    <polygon points="60,155 100,95 140,155" fill="#0b6623" />
    <polygon points="70,130 100,70 130,130" fill="#0b6623" />
    <polygon points="100,54.11 105.04,67.07 118.72,67.07 108.64,75.71 113.68,88.67 100,80.03 86.32,88.67 91.36,75.71 81.28,67.07 94.96,67.07" fill="#ffd54a" />
    <path d="M74,128 C84,117 116,117 126,128" fill="none" stroke="#8fbf5f" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity="0.95" />
    <path d="M64,155 C80,142 120,142 136,155" fill="none" stroke="#6aa144" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity="0.95" />
    <g stroke="#8b0000" stroke-width="0.8">
      <ellipse cx="92" cy="98" rx="4" ry="4.6" fill="#b71c1c" />
      <circle cx="118" cy="118" r="3.6" fill="#b71c1c" />
    </g>
    <g stroke="#b58a00" stroke-width="0.6">
      <circle cx="76" cy="126" r="3.2" fill="#ffd54a" />
      <circle cx="128" cy="138" r="2.8" fill="#fff176" />
    </g>
    <circle cx="106" cy="112" r="2.6" fill="#1976D2" />
    <circle cx="84" cy="140" r="2.2" fill="#2196F3" />
    <circle cx="104" cy="92" r="1.8" fill="#ffffff" opacity="0.95" />
    <circle cx="88" cy="118" r="1.6" fill="#fff8e1" opacity="0.95" />
    <circle cx="112" cy="142" r="1.6" fill="#ffe082" opacity="0.95" />
    <g id="xmas-bow" aria-hidden="true">
      <path d="M92,158 C86,150 88,142 96,150 C100,154 96,158 92,158" fill="#e53935" stroke="#7b1f1f" stroke-width="0.7" />
      <path d="M108,158 C114,150 112,142 104,150 C100,154 104,158 108,158" fill="#e53935" stroke="#7b1f1f" stroke-width="0.7" />
      <path d="M96,162 C92,168 84,174 78,180" fill="none" stroke="#c62828" stroke-width="2" stroke-linecap="round" />
      <path d="M104,162 C108,168 116,174 122,180" fill="none" stroke="#c62828" stroke-width="2" stroke-linecap="round" />
      <circle cx="100" cy="156" r="2.6" fill="#7b1f1f" />
      <circle cx="101" cy="155.2" r="0.7" fill="#fff8e1" opacity="0.9" />
    </g>
    <circle cx="116" cy="116" r="0.9" fill="#ffffff" opacity="0.9" />
    <circle cx="92" cy="96" r="0.8" fill="#ffffff" opacity="0.9" />
</g>"##;

const SNOWMAN: &str = r##"<g>
    <circle cx="100" cy="160" r="35" fill="#ffffff" stroke="#e0e0e0" stroke-width="1.5"/>
    <circle cx="100" cy="110" r="28" fill="#ffffff" stroke="#e0e0e0" stroke-width="1.5"/>
    <circle cx="100" cy="65" r="22" fill="#ffffff" stroke="#e0e0e0" stroke-width="1.5"/>
    <ellipse cx="100" cy="48" rx="28" ry="5" fill="#2c2c2c"/>
    <rect x="80" y="25" width="40" height="23" fill="#2c2c2c" rx="2"/>
    <rect x="80" y="40" width="40" height="4" fill="#b71c1c"/>
    <circle cx="92" cy="62" r="2.5" fill="#2c2c2c"/>
    <circle cx="108" cy="62" r="2.5" fill="#2c2c2c"/>
    <polygon points="100,68 105,70 100,72" fill="#ff6f00"/>
    <circle cx="92" cy="75" r="1.5" fill="#2c2c2c"/>
    <circle cx="96" cy="77" r="1.5" fill="#2c2c2c"/>
    <circle cx="100" cy="78" r="1.5" fill="#2c2c2c"/>
    <circle cx="104" cy="77" r="1.5" fill="#2c2c2c"/>
    <circle cx="108" cy="75" r="1.5" fill="#2c2c2c"/>
    <circle cx="100" cy="100" r="3" fill="#2c2c2c"/>
    <circle cx="100" cy="115" r="3" fill="#2c2c2c"/>
    <circle cx="100" cy="130" r="3" fill="#2c2c2c"/>
    <path d="M78,80 Q100,85 122,80" fill="none" stroke="#b71c1c" stroke-width="6" stroke-linecap="round"/>
    <path d="M78,84 Q100,89 122,84" fill="none" stroke="#c62828" stroke-width="4" stroke-linecap="round"/>
    <path d="M78,80 L70,95 L72,100" fill="#b71c1c" stroke="#8b0000" stroke-width="0.8"/>
</g>"##;

const SANTA: &str = r##"<g>
    <circle cx="100" cy="100" r="45" fill="#fdd0b5"/>
    <path d="M60,72 Q100,37 140,72 L140,82 Q100,87 60,82 Z" fill="#b71c1c"/>
    <ellipse cx="100" cy="82" rx="42" ry="6" fill="#ffffff"/>
    <circle cx="100" cy="49" r="8" fill="#ffffff"/>
    <circle cx="85" cy="95" r="4" fill="#2c2c2c"/>
    <circle cx="115" cy="95" r="4" fill="#2c2c2c"/>
    <circle cx="70" cy="105" r="7" fill="#ff8a80" opacity="0.6"/>
    <circle cx="130" cy="105" r="7" fill="#ff8a80" opacity="0.6"/>
    <ellipse cx="100" cy="105" rx="5" ry="6" fill="#ff6b6b"/>
    <ellipse cx="87" cy="115" rx="12" ry="5" fill="#ffffff"/>
    <ellipse cx="113" cy="115" rx="12" ry="5" fill="#ffffff"/>
    <path d="M70,120 Q100,155 130,120 Q125,140 100,145 Q75,140 70,120" fill="#ffffff"/>
    <circle cx="80" cy="130" r="5" fill="#f5f5f5"/>
    <circle cx="100" cy="138" r="5" fill="#f5f5f5"/>
    <circle cx="120" cy="130" r="5" fill="#f5f5f5"/>
    <path d="M92,124 Q100,128 108,124" fill="none" stroke="#8b4513" stroke-width="1.5" stroke-linecap="round"/>
</g>"##;

const GIFT: &str = r##"<g>
    <rect x="60" y="100" width="80" height="70" fill="#b71c1c" stroke="#8b0000" stroke-width="1.5" rx="3"/>
    <rect x="95" y="100" width="10" height="70" fill="#ffd54a"/>
    <rect x="60" y="130" width="80" height="10" fill="#ffd54a"/>
    <ellipse cx="85" cy="95" rx="12" ry="8" fill="#ffd54a" stroke="#daa520" stroke-width="1"/>
    <ellipse cx="115" cy="95" rx="12" ry="8" fill="#ffd54a" stroke="#daa520" stroke-width="1"/>
    <circle cx="100" cy="95" r="6" fill="#ffb300"/>
    <path d="M85,103 L78,115 L80,118" fill="#ffd54a" stroke="#daa520" stroke-width="0.8"/>
    <path d="M115,103 L122,115 L120,118" fill="#ffd54a" stroke="#daa520" stroke-width="0.8"/>
    <rect x="62" y="102" width="3" height="20" fill="#ffffff" opacity="0.3"/>
    <rect x="96" y="102" width="2" height="15" fill="#ffffff" opacity="0.5"/>
</g>"##;

const STAR: &str = r##"<g>
    <polygon points="100,50 110,85 145,90 120,112 128,147 100,130 72,147 80,112 55,90 90,85" fill="#ffd54a" stroke="#daa520" stroke-width="2"/>
    <polygon points="100,70 105,90 120,93 110,105 113,120 100,110 87,120 90,105 80,93 95,90" fill="#fff176"/>
    <circle cx="100" cy="100" r="8" fill="#ffeb3b"/>
</g>"##;

const CANDY_CANE: &str = r##"<g transform="translate(230,12) scale(-1,1)">
    <path d="M100,180 L100,100 Q100,70 120,70 Q140,70 140,90 Q140,110 120,110" fill="none" stroke="#ffffff" stroke-width="16" stroke-linecap="round"/>
    <path d="M100,175 L100,162" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M100,150 L100,136" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M100,125 L100,110" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M102,96 Q102,70 120,70" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M122,72 Q132,72 132,84" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M132,96 Q132,103 124,105" stroke="#b71c1c" stroke-width="16" stroke-linecap="round"/>
    <path d="M95,170 L95,105" stroke="#ffffff" stroke-width="3" opacity="0.6" stroke-linecap="round"/>
</g>"##;

const BELL: &str = r##"<g>
    <path d="M72,100 Q72,82 100,82 Q128,82 128,100 L132,126 Q132,134 122,140 L122,144 Q122,148 100,148 Q78,148 78,144 L78,140 Q68,134 68,126 Z" fill="#ffd54a" stroke="#d3a21a" stroke-width="1.5"/>
    <ellipse cx="100" cy="148" rx="26" ry="7" fill="#d3a21a"/>
    <ellipse cx="100" cy="156" rx="5" ry="6" fill="#8b0000"/>
    <path d="M90,80 Q100,76 110,80" fill="none" stroke="#b71c1c" stroke-width="3.5" stroke-linecap="round"/>
    <circle cx="88" cy="78" r="4.5" fill="#b71c1c"/>
    <circle cx="112" cy="78" r="4.5" fill="#b71c1c"/>
    <ellipse cx="86" cy="94" rx="10" ry="16" fill="#ffffff" opacity="0.45"/>
    <path d="M76,108 Q80,126 84,136" fill="none" stroke="#ffffff" stroke-width="2.5" opacity="0.35"/>
    <circle cx="95" cy="82" r="3" fill="#b71c1c"/>
    <circle cx="105" cy="82" r="3" fill="#b71c1c"/>
    <ellipse cx="92" cy="79" rx="4" ry="3" fill="#2e7d32"/>
    <ellipse cx="100" cy="78" rx="4" ry="3" fill="#2e7d32"/>
    <ellipse cx="108" cy="79" rx="4" ry="3" fill="#2e7d32"/>
</g>"##;

pub(crate) fn value_after(
    args: &[String],
    option: &str,
    default: &str,
) -> Result<String, std::io::Error> {
    match args.iter().position(|arg| arg == option) {
        Some(index) => args
            .get(index + 1)
            .cloned()
            .ok_or_else(|| std::io::Error::other(format!("{option} requires a value"))),
        None => Ok(default.to_string()),
    }
}

fn float_after(args: &[String], option: &str, default: f64) -> Result<f64, std::io::Error> {
    value_after(args, option, &default.to_string())?
        .parse()
        .map_err(|_| std::io::Error::other(format!("{option} must be a number")))
}

fn cli_options(args: &[String]) -> Result<QrOptions, std::io::Error> {
    let mut options = QrOptions::default();
    options.foreground = value_after(
        args,
        "--foreground-color",
        &value_after(args, "--foreground", DEFAULT_FOREGROUND)?,
    )?;
    options.background = value_after(
        args,
        "--background-color",
        &value_after(args, "--background", "#ffffff")?,
    )?;
    options.decorate = !args.iter().any(|arg| arg == "--no-decorate");
    options.logo_size = float_after(args, "--logo-size", 20.0)?;
    options.overlay_multiplier = float_after(args, "--overlay-mult", 3.0)?;
    options.overlay_shift_x = float_after(args, "--overlay-shift-x", 0.90)?;
    options.overlay_shift_y = float_after(args, "--overlay-shift-y", 0.50)?;
    options.tree_style = value_after(args, "--tree-style", "fancy")?;
    options.decoration_type = value_after(args, "--decoration-type", "tree")?;
    options.ecc = match value_after(args, "--ecc", "H")?.to_ascii_uppercase().as_str() {
        "L" => EcLevel::L,
        "M" => EcLevel::M,
        "Q" => EcLevel::Q,
        "H" => EcLevel::H,
        _ => return Err(std::io::Error::other("--ecc must be one of L, M, Q, H")),
    };
    Ok(options)
}

pub fn sanitize_svg_for_html(svg: &str, pretty: bool, indent_spaces: usize) -> String {
    let cleaned = svg
        .lines()
        .filter(|line| !line.trim_start().starts_with("<?xml"))
        .filter(|line| !line.trim_start().to_ascii_uppercase().starts_with("<!DOCTYPE"))
        .filter(|line| !line.trim().is_empty())
        .collect::<Vec<_>>();
    if !pretty {
        return format!("{}\n", cleaned.iter().map(|line| line.trim()).collect::<String>());
    }
    if cleaned.len() < 2 {
        return format!("{}\n", cleaned.join("\n"));
    }
    let indent = " ".repeat(indent_spaces);
    let mut output = vec![cleaned[0].trim().to_string()];
    output.extend(
        cleaned[1..cleaned.len() - 1]
            .iter()
            .map(|line| format!("{indent}{}", line.trim())),
    );
    output.push(cleaned[cleaned.len() - 1].trim().to_string());
    format!("{}\n", output.join("\n"))
}

pub fn generate_cli(args: &[String]) -> Result<u8, Box<dyn std::error::Error>> {
    let root_domain = value_after(
        args,
        "--root-domain",
        &std::env::var("ROOT_DOMAIN").unwrap_or_else(|_| "https://example.com".to_string()),
    )?;
    let pattern = value_after(args, "--pattern", "*.html")?;
    let output_dir = PathBuf::from(value_after(args, "--out-dir", "scripts/generated_qr")?);
    let indent = value_after(args, "--indent", "2")?.parse::<usize>()?;
    if ![2, 4].contains(&indent) {
        return Err("--indent must be 2 or 4".into());
    }
    let minify = args.iter().any(|arg| arg == "--minify");
    let defaults = cli_options(args)?;
    fs::create_dir_all(&output_dir)?;
    let mut html_files = fs::read_dir(".")?
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| path.is_file())
        .filter(|path| {
            path.file_name()
                .and_then(|name| name.to_str())
                .is_some_and(|name| matches_pattern(&pattern, name))
        })
        .collect::<Vec<_>>();
    html_files.sort();
    if html_files.is_empty() {
        println!("No files found matching pattern");
        return Ok(0);
    }
    for path in html_files {
        let filename = path.file_name().and_then(|name| name.to_str()).unwrap_or_default();
        let basename = path.file_stem().and_then(|name| name.to_str()).unwrap_or_default();
        let public_url = format!(
            "{}/{}",
            root_domain.trim_end_matches('/'),
            url_encode_path(filename)
        );
        let mut options = defaults.clone();
        let meta = read_meta_tags_from_html(&path);
        if let Some(value) = meta.get("qr-foreground-color") {
            options.foreground.clone_from(value);
        }
        if let Some(value) = meta.get("qr-background-color") {
            options.background.clone_from(value);
        }
        if let Some(value) = meta.get("qr-decorate") {
            options.decorate = matches!(value.trim().to_ascii_lowercase().as_str(), "1" | "true" | "yes");
        }
        if let Some(value) = meta.get("qr-tree-style") {
            if matches!(value.trim().to_ascii_lowercase().as_str(), "fancy" | "plain") {
                options.tree_style = value.trim().to_ascii_lowercase();
            }
        }
        if let Some(value) = meta.get("qr-decoration-type") {
            if ["tree", "snowman", "santa", "gift", "star", "candy-cane", "bell"]
                .contains(&value.trim().to_ascii_lowercase().as_str())
            {
                options.decoration_type = value.trim().to_ascii_lowercase();
            }
        }
        let svg = generate_svg(&public_url, &options).map_err(|message| {
            std::io::Error::other(format!(
                "cannot generate QR for {}: {message}",
                path.display()
            ))
        })?;
        let output_path = output_dir.join(format!("{basename}.svg"));
        fs::write(
            &output_path,
            sanitize_svg_for_html(&svg, !minify, indent),
        )?;
        println!("Generated {} for {public_url}", output_path.display());
    }
    Ok(0)
}

pub fn inject_svg(svg_content: &str, html_path: &Path, preserve_manual: bool) -> Result<bool, String> {
    let content = fs::read_to_string(html_path)
        .map_err(|error| format!("cannot read {}: {error}", html_path.display()))?;
    let Some(start) = content.find(MARKER_START) else {
        println!("Markers not found in {}; skipping", html_path.display());
        return Ok(false);
    };
    let Some(relative_end) = content[start + MARKER_START.len()..].find(MARKER_END) else {
        println!("Markers not found in {}; skipping", html_path.display());
        return Ok(false);
    };
    let end = start + MARKER_START.len() + relative_end;
    let existing = &content[start + MARKER_START.len()..end];
    if preserve_manual && !existing.trim().is_empty() {
        println!("Manual content detected in {}; skipping.", html_path.display());
        return Ok(false);
    }
    let line_start = content[..start].rfind('\n').map_or(0, |index| index + 1);
    let leading_ws = content[line_start..start]
        .chars()
        .take_while(|character| matches!(character, ' ' | '\t'))
        .collect::<String>();
    let indented = svg_content
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| format!("{leading_ws}{line}"))
        .collect::<Vec<_>>()
        .join("\n");
    let new_content = format!(
        "{}\n{}\n{}{}",
        &content[..start + MARKER_START.len()],
        indented,
        leading_ws,
        &content[end..]
    );
    if new_content == content {
        println!("No changes for {}", html_path.display());
        return Ok(false);
    }
    fs::write(html_path, new_content)
        .map_err(|error| format!("cannot write {}: {error}", html_path.display()))?;
    println!("Injected SVG into {}", html_path.display());
    Ok(true)
}

pub fn inject_cli(args: &[String]) -> Result<u8, Box<dyn std::error::Error>> {
    let svg_dir = PathBuf::from(value_after(args, "--svg-dir", "scripts/generated_qr")?);
    let pattern = value_after(args, "--pattern", "*.html")?;
    let preserve_manual = args.iter().any(|arg| arg == "--preserve-manual");
    let mut svg_files = fs::read_dir(&svg_dir)
        .map_err(|error| format!("cannot read {}: {error}", svg_dir.display()))?
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| path.extension().is_some_and(|ext| ext == "svg"))
        .collect::<Vec<_>>();
    svg_files.sort();
    if svg_files.is_empty() {
        println!("No SVG files found to inject");
        return Ok(0);
    }
    let mut updated = 0;
    for svg_path in svg_files {
        let basename = svg_path.file_stem().and_then(|name| name.to_str()).unwrap_or_default();
        let html_path = PathBuf::from(format!("{basename}.html"));
        if !matches_pattern(&pattern, html_path.file_name().and_then(|name| name.to_str()).unwrap_or_default()) {
            continue;
        }
        if !html_path.exists() {
            println!(
                "No matching HTML file for {}; expected {}; skipping",
                svg_path.display(),
                html_path.display()
            );
            continue;
        }
        let svg = fs::read_to_string(&svg_path)?;
        if inject_svg(&svg, &html_path, preserve_manual).map_err(std::io::Error::other)? {
            updated += 1;
        }
    }
    println!("Done — injected into {updated} files");
    Ok(0)
}

pub fn check_svg_cli(_args: &[String]) -> Result<u8, Box<dyn std::error::Error>> {
    let path = Path::new("scripts/generated_qr/index.svg");
    let content = match fs::read_to_string(path) {
        Ok(content) => content,
        Err(error) => {
            eprintln!("ERROR: cannot read {}: {error}", path.display());
            return Ok(2);
        }
    };
    let checks = [
        ("star", "points=\"100,54.11"),
        ("bow_left", "M92,158"),
        ("bow_right", "M108,158"),
        ("garland", "M74,128"),
        ("ellipse", "ellipse cx=\"92\""),
        ("gloss", "circle cx=\"116\""),
    ];
    let mut all_ok = true;
    for (name, fragment) in checks {
        let found = content.contains(fragment);
        println!("{name}: {}", if found { "OK" } else { "MISSING" });
        all_ok &= found;
    }
    Ok(if all_ok { 0 } else { 3 })
}

pub fn regenerate_reference_cli() -> Result<u8, Box<dyn std::error::Error>> {
    fs::create_dir_all("tests")?;
    for (filename, url, foreground, background, decoration_type) in [
        ("reference_qr.svg", "https://example.com/index.html", "#0b6623", "#ffffff", "tree"),
        ("reference_elsa_qr.svg", "https://example.com/elsa.html", "#1565C0", "#e3f2fd", "snowman"),
    ] {
        let options = QrOptions {
            foreground: foreground.to_string(),
            background: background.to_string(),
            decoration_type: decoration_type.to_string(),
            ..QrOptions::default()
        };
        let svg = generate_svg(url, &options)
            .map_err(|message| std::io::Error::other(format!("{filename}: {message}")))?;
        fs::write(
            Path::new("tests").join(filename),
            sanitize_svg_for_html(&svg, true, 2),
        )?;
        println!("Wrote tests/{filename}");
    }
    Ok(0)
}

#[cfg(test)]
mod tests {
    use super::{generate_svg, inject_svg, read_meta_tags_from_html, sanitize_svg_for_html, QrOptions};
    use crate::{MARKER_END, MARKER_START};
    use std::fs;

    #[test]
    fn generated_svg_has_current_color_and_requested_decoration() {
        let options = QrOptions {
            foreground: "#112233".to_string(),
            decoration_type: "gift".to_string(),
            ..QrOptions::default()
        };
        let svg = generate_svg("https://example.com/test", &options).unwrap();
        assert!(svg.contains("fill=\"currentColor\""));
        assert!(svg.contains("data-qr-default-foreground-color=\"#112233\""));
        assert!(svg.contains("id=\"xmas-decoration\""));
        assert!(svg.contains("fill=\"#b71c1c\""));
    }

    #[test]
    fn all_decorations_and_tree_styles_are_supported() {
        for decoration_type in ["tree", "snowman", "santa", "gift", "star", "candy-cane", "bell"] {
            let options = QrOptions {
                decoration_type: decoration_type.to_string(),
                ..QrOptions::default()
            };
            let svg = generate_svg("https://example.com/test", &options).unwrap();
            assert!(svg.contains("id=\"xmas-decoration\""), "{decoration_type}");
            assert!(svg.len() > 500, "{decoration_type}");
        }
        let plain = QrOptions {
            tree_style: "plain".to_string(),
            ..QrOptions::default()
        };
        assert!(!generate_svg("https://example.com/plain", &plain)
            .unwrap()
            .contains("xmas-bow"));
    }

    #[test]
    fn qr_without_decoration_keeps_a_quiet_zone() {
        let options = QrOptions {
            decorate: false,
            ..QrOptions::default()
        };
        let svg = generate_svg("https://example.com/plain", &options).unwrap();
        assert!(!svg.contains("xmas-decoration"));
        assert!(svg.contains("viewBox=\"0 0 "));
        assert!(svg.contains("M8 8"));
    }

    #[test]
    fn sanitizer_supports_pretty_and_minified_output() {
        let svg = "<svg>\n<path/>\n</svg>\n";
        assert!(sanitize_svg_for_html(svg, true, 2).contains("\n  <path"));
        assert!(!sanitize_svg_for_html(svg, false, 2).trim_end().contains('\n'));
    }

    #[test]
    fn injector_preserves_manual_content_and_marker_indentation() {
        let temp = std::env::temp_dir().join(format!("simplewish-{}.html", std::process::id()));
        fs::write(&temp, format!("start\n\t{MARKER_START}\n\t\n\t{MARKER_END}\nend\n")).unwrap();
        assert!(inject_svg("<svg>\n<path/>\n</svg>", &temp, false).unwrap());
        let content = fs::read_to_string(&temp).unwrap();
        assert!(content.contains("\n\t<svg"));
        assert!(content.contains(MARKER_END));
        assert!(!inject_svg("<svg/>", &temp, true).unwrap());
        let _ = fs::remove_file(temp);
    }

    #[test]
    fn metadata_ignores_comments_and_reads_known_keys() {
        let temp = std::env::temp_dir().join(format!("simplewish-meta-{}.html", std::process::id()));
        fs::write(
            &temp,
            "<!-- <meta name=\"qr-decorate\" content=\"true\"> -->\
             <meta content='#abc123' name='qr-foreground-color'>\
             <meta name=\"unknown\" content=\"no\">",
        )
        .unwrap();
        let tags = read_meta_tags_from_html(&temp);
        assert_eq!(tags.get("qr-foreground-color").map(String::as_str), Some("#abc123"));
        assert!(!tags.contains_key("qr-decorate"));
        let _ = fs::remove_file(temp);
    }
}
