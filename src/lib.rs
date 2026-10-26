pub mod automation;
pub mod qr;
pub mod recipient;

pub const MARKER_START: &str = "<!-- QR-PLACEHOLDER-START -->";
pub const MARKER_END: &str = "<!-- QR-PLACEHOLDER-END -->";

pub fn html_escape(value: &str, quote: bool) -> String {
    let mut escaped = String::with_capacity(value.len());
    for character in value.chars() {
        match character {
            '&' => escaped.push_str("&amp;"),
            '<' => escaped.push_str("&lt;"),
            '>' => escaped.push_str("&gt;"),
            '"' if quote => escaped.push_str("&quot;"),
            '\'' if quote => escaped.push_str("&#x27;"),
            _ => escaped.push(character),
        }
    }
    escaped
}

pub fn url_encode_path(value: &str) -> String {
    let mut encoded = String::with_capacity(value.len());
    for byte in value.bytes() {
        if byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.' | b'~') {
            encoded.push(byte as char);
        } else {
            encoded.push_str(&format!("%{byte:02X}"));
        }
    }
    encoded
}

pub fn matches_pattern(pattern: &str, filename: &str) -> bool {
    if pattern == "*" || pattern == filename {
        return true;
    }
    if let Some(extension) = pattern.strip_prefix("*.") {
        return filename.ends_with(&format!(".{extension}"));
    }
    let mut pattern_chars = pattern.chars().peekable();
    let mut name_chars = filename.chars().peekable();
    while let Some(pattern_char) = pattern_chars.next() {
        match pattern_char {
            '*' => {
                if pattern_chars.peek().is_none() {
                    return true;
                }
                let remaining: String = pattern_chars.collect();
                return filename[name_chars.collect::<String>().len()..].contains(&remaining);
            }
            '?' => {
                if name_chars.next().is_none() {
                    return false;
                }
            }
            literal if Some(literal) != name_chars.next() => return false,
            _ => {}
        }
    }
    name_chars.next().is_none()
}

#[cfg(test)]
mod tests {
    use super::{html_escape, matches_pattern, url_encode_path};

    #[test]
    fn escapes_text_and_attributes() {
        assert_eq!(html_escape("A & <B>", false), "A &amp; &lt;B&gt;");
        assert_eq!(html_escape("'\"&", true), "&#x27;&quot;&amp;");
    }

    #[test]
    fn encodes_url_path_segments() {
        assert_eq!(url_encode_path("winter list.html"), "winter%20list.html");
    }

    #[test]
    fn matches_common_file_patterns() {
        assert!(matches_pattern("*.html", "index.html"));
        assert!(!matches_pattern("*.html", "index.svg"));
        assert!(matches_pattern("index.html", "index.html"));
    }
}
