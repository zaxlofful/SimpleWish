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
    let pattern = pattern.chars().collect::<Vec<_>>();
    let text = filename.chars().collect::<Vec<_>>();
    let (mut pattern_index, mut text_index) = (0, 0);
    let (mut last_star, mut star_match) = (None, 0);
    while text_index < text.len() {
        if pattern
            .get(pattern_index)
            .is_some_and(|character| *character == '?' || *character == text[text_index])
        {
            pattern_index += 1;
            text_index += 1;
        } else if pattern.get(pattern_index) == Some(&'*') {
            last_star = Some(pattern_index);
            pattern_index += 1;
            star_match = text_index;
        } else if let Some(star) = last_star {
            star_match += 1;
            text_index = star_match;
            pattern_index = star + 1;
        } else {
            return false;
        }
    }
    while pattern.get(pattern_index) == Some(&'*') {
        pattern_index += 1;
    }
    pattern_index == pattern.len()
}

#[cfg(test)]
mod tests {
    use super::{html_escape, matches_pattern, url_encode_path};

    #[test]
    fn escapes_text_and_attributes() {
        assert_eq!(html_escape("A & <B>", false), "A &amp; &lt;B&gt;");
        assert_eq!(html_escape("'\"&", true), "&#x27;&quot;&amp;");
        assert_eq!(html_escape("'\"", false), "'\"");
    }

    #[test]
    fn encodes_url_path_segments() {
        assert_eq!(url_encode_path("winter list.html"), "winter%20list.html");
        assert_eq!(
            url_encode_path("a/b?x=1&y=🎄"),
            "a%2Fb%3Fx%3D1%26y%3D%F0%9F%8E%84"
        );
        assert_eq!(url_encode_path("-_.~AZaz09"), "-_.~AZaz09");
    }

    #[test]
    fn matches_common_file_patterns() {
        assert!(matches_pattern("*.html", "index.html"));
        assert!(!matches_pattern("*.html", "index.svg"));
        assert!(matches_pattern("index.html", "index.html"));
        assert!(matches_pattern("list-?.html", "list-1.html"));
        assert!(matches_pattern("*.html", "winter🎄.html"));
        assert!(!matches_pattern("list-?.html", "list-.html"));
        assert!(matches_pattern("a*b", "axxxb"));
        assert!(!matches_pattern("a*b", "axxxc"));
        assert!(matches_pattern("a**b", "ab"));
        assert!(matches_pattern("*", ""));
        assert!(!matches_pattern("", "x"));
    }
}
