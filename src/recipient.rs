use serde_json::Value;
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

use crate::html_escape;

fn string_value(value: &Value) -> String {
    match value {
        Value::String(value) => value.clone(),
        Value::Null => String::new(),
        other => other.to_string(),
    }
}

fn replace_section(text: &mut String, start_tag: &str, end_tag: &str, replacement: &str) {
    let Some(start) = text.find(start_tag) else {
        return;
    };
    let body_start = start + start_tag.len();
    let Some(relative_end) = text[body_start..].find(end_tag) else {
        return;
    };
    let body_end = body_start + relative_end;
    text.replace_range(body_start..body_end, replacement);
}

fn replace_css_variable(text: &mut String, variable: &str, value: &str) {
    if !valid_hex_color(value) {
        return;
    }
    let Some(start) = text.find(variable) else {
        return;
    };
    let value_start = start + variable.len();
    let Some(relative_end) = text[value_start..].find([';', '}']) else {
        return;
    };
    text.replace_range(value_start..value_start + relative_end, value);
}

fn valid_hex_color(value: &str) -> bool {
    let value = value.strip_prefix('#').unwrap_or_default();
    matches!(value.len(), 3 | 6) && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn safe_link(value: &str) -> bool {
    let value = value.trim();
    !value.bytes().any(|byte| byte.is_ascii_control())
        && ["https://", "http://", "mailto:"].iter().any(|scheme| {
            value
                .get(..scheme.len())
                .is_some_and(|prefix| prefix.eq_ignore_ascii_case(scheme))
        })
}

fn json_field<'a>(data: &'a Value, key: &str) -> Option<&'a Value> {
    data.get(key)
}

pub fn render_from_template(template: &str, data: &Value) -> String {
    let mut rendered = template.to_string();
    let mut meta = Vec::new();
    for (field, key) in [
        ("qr_foreground", "qr-foreground-color"),
        ("qr_background", "qr-background-color"),
        ("qr_decor_type", "qr-decoration-type"),
        ("qr_tree_style", "qr-tree-style"),
    ] {
        if let Some(value) = json_field(data, field)
            .filter(|value| !value.is_null() && !string_value(value).is_empty())
        {
            meta.push(format!(
                "<meta name=\"{key}\" content=\"{}\">",
                html_escape(&string_value(value), true)
            ));
        }
    }
    if let Some(value) = json_field(data, "qr_decorate") {
        let content = match value {
            Value::Bool(true) => "true".to_string(),
            Value::Bool(false) => "false".to_string(),
            other => {
                let text = string_value(other);
                match text.trim().to_ascii_lowercase().as_str() {
                    "true" | "false" => text.trim().to_ascii_lowercase(),
                    _ => text,
                }
            }
        };
        meta.push(format!(
            "<meta name=\"qr-decorate\" content=\"{}\">",
            html_escape(&content, true)
        ));
    }
    if !meta.is_empty()
        && let Some(start) = rendered.find("<!-- QR metadata:")
        && let Some(relative_end) = rendered[start..].find("-->")
    {
        let end = start + relative_end + 3;
        rendered.insert_str(end, &format!("\n  {}", meta.join("\n  ")));
    }

    if let Some(title) = json_field(data, "title") {
        replace_section(
            &mut rendered,
            "<title>",
            "</title>",
            &html_escape(&string_value(title), true),
        );
    }
    if let Some(recipient) = json_field(data, "recipient") {
        let safe = html_escape(&string_value(recipient), true);
        replace_section(
            &mut rendered,
            "<h1 id=\"recipient\">",
            "</h1>",
            &format!("Christmas List for {safe}"),
        );
    }
    if let Some(subtitle) = json_field(data, "sub") {
        replace_section(
            &mut rendered,
            "<p class=\"sub\">",
            "</p>",
            &html_escape(&string_value(subtitle), true),
        );
    }
    for (field, variable) in [("accent", "--accent:"), ("muted", "--muted:")] {
        if let Some(value) = json_field(data, field) {
            replace_css_variable(&mut rendered, variable, &string_value(value));
        }
    }
    if let Some(hint) = json_field(data, "hint") {
        replace_section(
            &mut rendered,
            "<p class=\"hint\">",
            "</p>",
            &html_escape(&string_value(hint), true),
        );
    }
    if let Some(Value::Array(gifts)) = json_field(data, "gifts") {
        let mut list = String::new();
        for gift in gifts {
            let text = gift.get("text").map(string_value).unwrap_or_default();
            let safe_text = html_escape(&text, true);
            if let Some(href) = gift
                .get("href")
                .filter(|href| !href.is_null() && safe_link(&string_value(href)))
            {
                list.push_str(&format!(
                    "          <li><a href=\"{}\" target=\"_blank\" rel=\"noopener\">{safe_text}</a></li>\n",
                    html_escape(&string_value(href), true)
                ));
            } else {
                list.push_str(&format!("          <li>{safe_text}</li>\n"));
            }
        }
        if let Some(start) = rendered.find("<ul id=\"gift-list\"")
            && let Some(tag_end_relative) = rendered[start..].find('>')
        {
            let content_start = start + tag_end_relative + 1;
            if let Some(end) = rendered[content_start..].find("</ul>") {
                let content_end = content_start + end;
                rendered.replace_range(content_start..content_end, &format!("\n{list}        "));
            }
        }
    }
    if let Some(notes) = json_field(data, "notes")
        && let Some(section) = rendered.find("<section class=\"notes\">")
        && let Some(start_relative) = rendered[section..].find("<p>")
    {
        let start = section + start_relative + 3;
        if let Some(end_relative) = rendered[start..].find("</p>") {
            let end = start + end_relative;
            rendered.replace_range(start..end, &html_escape(&string_value(notes), true));
        }
    }
    if let Some(start) = rendered.find(crate::MARKER_START)
        && let Some(relative_end) =
            rendered[start + crate::MARKER_START.len()..].find(crate::MARKER_END)
    {
        let content_start = start + crate::MARKER_START.len();
        let content_end = content_start + relative_end;
        rendered.replace_range(content_start..content_end, "\n");
    }
    rendered
}

fn render_file(template: &str, data_path: &Path, output: Option<&Path>) -> Result<PathBuf, String> {
    let contents = fs::read_to_string(data_path)
        .map_err(|error| format!("cannot read {}: {error}", data_path.display()))?;
    let data: Value = serde_json::from_str(&contents)
        .map_err(|error| format!("cannot parse {}: {error}", data_path.display()))?;
    let output_path = output.map_or_else(
        || {
            let name = data_path
                .file_stem()
                .and_then(|value| value.to_str())
                .unwrap_or("output");
            PathBuf::from(format!("{name}.html"))
        },
        Path::to_path_buf,
    );
    fs::write(&output_path, render_from_template(template, &data))
        .map_err(|error| format!("cannot write {}: {error}", output_path.display()))?;
    println!("Wrote {}", output_path.display());
    Ok(output_path)
}

pub fn generate_cli(args: &[String]) -> Result<u8, Box<dyn std::error::Error>> {
    if args.iter().any(|arg| arg == "--help" || arg == "-h") {
        println!(
            "Usage: simplewish generate-recipient [--data FILE | --bulk] \
             [--template FILE] [--out FILE] [--recipients-dir DIR]"
        );
        return Ok(0);
    }
    let mut seen = HashSet::new();
    let mut bulk = false;
    let mut data_path = None;
    let mut template_path = PathBuf::from("index.html");
    let mut output = None;
    let mut recipients_dir = None;
    let mut index = 0;
    while index < args.len() {
        let option = args[index].as_str();
        if !seen.insert(option.to_string()) {
            return Err(std::io::Error::other(format!(
                "option {option} may only be specified once"
            ))
            .into());
        }
        match option {
            "--bulk" => {
                bulk = true;
                index += 1;
            }
            "--data" | "--template" | "--out" | "--recipients-dir" => {
                let value = args
                    .get(index + 1)
                    .filter(|value| !value.starts_with('-') && !value.is_empty())
                    .ok_or_else(|| std::io::Error::other(format!("{option} requires a path")))?;
                match option {
                    "--data" => data_path = Some(PathBuf::from(value)),
                    "--template" => template_path = PathBuf::from(value),
                    "--out" => output = Some(PathBuf::from(value)),
                    "--recipients-dir" => recipients_dir = Some(PathBuf::from(value)),
                    _ => unreachable!(),
                }
                index += 2;
            }
            _ => {
                return Err(
                    std::io::Error::other(format!("unexpected argument `{option}`")).into(),
                );
            }
        }
    }
    if bulk && data_path.is_some() {
        return Err(std::io::Error::other("--data cannot be used with --bulk").into());
    }
    if !bulk && data_path.is_none() {
        return Err(std::io::Error::other("--data is required unless --bulk is specified").into());
    }
    if bulk && output.is_some() {
        return Err(std::io::Error::other("--out cannot be used with --bulk").into());
    }
    if !bulk && recipients_dir.is_some() {
        return Err(std::io::Error::other("--recipients-dir requires --bulk").into());
    }
    let template = fs::read_to_string(&template_path)?;
    if bulk {
        let recipients_dir = recipients_dir.unwrap_or_else(|| PathBuf::from("recipients"));
        if !recipients_dir.is_dir() {
            return Err(std::io::Error::other(format!(
                "No recipients directory found at {}",
                recipients_dir.display()
            ))
            .into());
        }
        let mut data_files = fs::read_dir(&recipients_dir)?
            .filter_map(Result::ok)
            .map(|entry| entry.path())
            .filter(|path| {
                path.extension()
                    .is_some_and(|extension| extension == "json")
            })
            .collect::<Vec<_>>();
        data_files.sort();
        if data_files.is_empty() {
            println!("No recipient JSON files found to generate");
            return Ok(0);
        }
        for data_path in data_files {
            render_file(&template, &data_path, None)?;
        }
        return Ok(0);
    }
    render_file(
        &template,
        data_path.as_deref().expect("required above"),
        output.as_deref(),
    )?;
    Ok(0)
}

#[cfg(test)]
mod tests {
    use super::render_from_template;
    use serde_json::Value;
    use serde_json::json;
    use std::fs;
    use std::path::{Path, PathBuf};

    #[test]
    fn css_replacement_preserves_following_rules_without_semicolon() {
        let mut text = "a{--muted:#abc}b{color:red;}".to_string();
        super::replace_css_variable(&mut text, "--muted:", "#def");
        assert_eq!(text, "a{--muted:#def}b{color:red;}");
    }

    #[test]
    fn renders_escaped_recipient_data_and_clears_qr_placeholder() {
        let template = "<title>Original</title><h1 id=\"recipient\">Original</h1>\
            <ul id=\"gift-list\"><li>Old</li></ul>\
            <!-- QR metadata: options -->\
            <!-- QR-PLACEHOLDER-START -->manual<!-- QR-PLACEHOLDER-END -->";
        let data = json!({
            "title": "Elsa's List",
            "recipient": "Elsa & Friends",
            "gifts": [{"text":"A <gift>","href":"https://example.com/?a=1&b=2"}],
            "qr_decorate": true,
            "qr_foreground":"#abc123",
            "qr_background":"#ffffff",
            "qr_decor_type":"gift",
            "qr_tree_style":"plain"
        });
        let html = render_from_template(template, &data);
        assert!(html.contains("<title>Elsa&#x27;s List</title>"));
        assert!(html.contains("Christmas List for Elsa &amp; Friends"));
        assert!(html.contains("A &lt;gift&gt;"));
        assert!(html.contains("a=1&amp;b=2"));
        assert!(html.contains("<meta name=\"qr-foreground-color\" content=\"#abc123\">"));
        assert!(html.contains("<meta name=\"qr-background-color\" content=\"#ffffff\">"));
        assert!(html.contains("<meta name=\"qr-decoration-type\" content=\"gift\">"));
        assert!(html.contains("<meta name=\"qr-tree-style\" content=\"plain\">"));
        assert!(html.contains("<meta name=\"qr-decorate\" content=\"true\">"));
        assert!(html.contains("<!-- QR-PLACEHOLDER-START -->\n<!-- QR-PLACEHOLDER-END -->"));
        assert!(!html.contains("<li>Old</li>"));
        assert!(html.contains(
            "<li><a href=\"https://example.com/?a=1&amp;b=2\" target=\"_blank\" rel=\"noopener\">A &lt;gift&gt;</a></li>"
        ));
    }

    #[test]
    fn checked_in_recipient_files_match_the_expected_schema() {
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("recipients");
        let files = fs::read_dir(root)
            .unwrap()
            .map(Result::unwrap)
            .filter(|entry| {
                let path = entry.path();
                path.is_file()
                    && path
                        .extension()
                        .is_some_and(|extension| extension == "json")
            })
            .collect::<Vec<_>>();
        assert!(
            !files.is_empty(),
            "at least one recipient JSON file is required"
        );
        for file in files {
            let data: Value =
                serde_json::from_str(&fs::read_to_string(file.path()).unwrap()).unwrap();
            assert!(
                data["recipient"]
                    .as_str()
                    .is_some_and(|value| !value.trim().is_empty())
            );
            assert!(
                data["title"]
                    .as_str()
                    .is_some_and(|value| !value.trim().is_empty())
            );
            assert!(
                data["gifts"]
                    .as_array()
                    .is_some_and(|gifts| !gifts.is_empty())
            );
            assert!(data["qr_decorate"].is_boolean());
            for field in [
                "qr_foreground",
                "qr_background",
                "qr_decor_type",
                "qr_tree_style",
            ] {
                assert!(
                    data.get(field).is_none_or(Value::is_string),
                    "{} in {} must be a string when present",
                    field,
                    file.path().display()
                );
            }
            for gift in data["gifts"].as_array().unwrap() {
                assert!(
                    gift["text"]
                        .as_str()
                        .is_some_and(|value| !value.trim().is_empty())
                );
                if let Some(href) = gift.get("href") {
                    assert!(href.as_str().is_some_and(|value| !value.trim().is_empty()));
                }
            }
        }
    }

    #[test]
    fn unsafe_links_and_css_values_are_not_rendered() {
        let template = "<a style=\"--accent: #123456;\" href=\"\">x</a>\
            <p style=\"--muted: #abc;\">muted</p>\
            <ul id=\"gift-list\"></ul>";
        let data = json!({
            "accent": "red; background: url(https://example.invalid)",
            "muted": "#gggggg",
            "gifts": [
                {"text":"unsafe","href":"javascript:alert(1)"},
                {"text":"safe","href":"https://example.com"},
                {"text":"mail","href":"mailto:friend@example.com"},
                {"text":"control","href":"https://example.com/\nheader"}
            ]
        });
        let html = render_from_template(template, &data);
        assert!(html.contains("--accent: #123456;"));
        assert!(html.contains("--muted: #abc;"));
        assert!(html.contains("<li>unsafe</li>"));
        assert!(!html.contains("href=\"javascript:"));
        assert!(html.contains("href=\"https://example.com\""));
        assert!(html.contains("href=\"mailto:friend@example.com\""));
        assert!(html.contains("<li>control</li>"));
    }

    #[test]
    fn value_and_section_helpers_handle_null_and_missing_markers() {
        assert_eq!(super::string_value(&json!("hello")), "hello");
        assert_eq!(super::string_value(&Value::Null), "");
        assert_eq!(super::string_value(&json!(42)), "42");

        let mut text = "before<title>old</title>after".to_string();
        super::replace_section(&mut text, "<title>", "</title>", "new");
        assert_eq!(text, "before<title>new</title>after");
        super::replace_section(&mut text, "<missing>", "</missing>", "ignored");
        super::replace_section(&mut text, "<title>", "</missing>", "ignored");
        assert_eq!(text, "before<title>new</title>after");
        assert_eq!(
            super::json_field(&json!({"key": 1}), "key").and_then(Value::as_i64),
            Some(1)
        );
        assert_eq!(super::json_field(&json!({}), "key"), None);
    }

    #[test]
    fn accepts_only_valid_hex_colors_and_safe_link_schemes() {
        for color in ["#abc", "#ABC", "#123456"] {
            assert!(super::valid_hex_color(color), "{color}");
        }
        for color in ["abc", "#12", "#12345", "#1234567", "#ggg", "#00000"] {
            assert!(!super::valid_hex_color(color), "{color}");
        }
        for link in [
            "https://example.com",
            "HTTP://example.com",
            "mailto:friend@example.com",
        ] {
            assert!(super::safe_link(link), "{link}");
        }
        for link in [
            "javascript:alert(1)",
            "data:text/html,x",
            "https://example.com/a\nb",
        ] {
            assert!(!super::safe_link(link), "{link:?}");
        }
    }

    #[test]
    fn renders_css_colors_only_when_valid_and_semicolon_is_present() {
        let mut text = "a{--accent:#123456;--muted:#abc}".to_string();
        super::replace_css_variable(&mut text, "--accent:", "#abcdef");
        super::replace_css_variable(&mut text, "--muted:", "#12345");
        assert_eq!(text, "a{--accent:#abcdef;--muted:#abc}");
        super::replace_css_variable(&mut text, "--missing:", "#fff");
        assert_eq!(text, "a{--accent:#abcdef;--muted:#abc}");
    }

    #[test]
    fn render_file_reads_json_and_writes_the_requested_output() {
        let base = std::env::temp_dir().join(format!("simplewish-render-{}", std::process::id()));
        let data_path = base.with_extension("json");
        let output_path = base.with_extension("html");
        fs::write(&data_path, r#"{"title":"Test title"}"#).unwrap();
        let result =
            super::render_file("<title>Old</title>", &data_path, Some(&output_path)).unwrap();
        assert_eq!(result, output_path);
        assert_eq!(
            fs::read_to_string(&output_path).unwrap(),
            "<title>Test title</title>"
        );

        fs::write(&data_path, "{invalid json").unwrap();
        assert!(
            super::render_file("template", &data_path, Some(&output_path))
                .unwrap_err()
                .contains("cannot parse")
        );
        assert!(
            super::render_file("template", &base.with_extension("missing"), None)
                .unwrap_err()
                .contains("cannot read")
        );
        let _ = fs::remove_file(data_path);
        let _ = fs::remove_file(output_path);
    }

    #[test]
    fn bulk_generation_writes_recipient_pages_to_current_directory() {
        let base = std::env::temp_dir().join(format!("simplewish-bulk-{}", std::process::id()));
        let recipients = base.join("recipients");
        let template = base.join("template.html");
        let stem = format!("bulk-recipient-{}", std::process::id());
        let name = format!("{stem}.html");
        let output = Path::new(&name);
        fs::create_dir_all(&recipients).unwrap();
        fs::write(&template, "<title>Old</title>").unwrap();
        fs::write(
            recipients.join(format!("{stem}.json")),
            r#"{"title":"Test"}"#,
        )
        .unwrap();
        assert_eq!(
            super::generate_cli(&[
                "--bulk".to_string(),
                "--template".to_string(),
                template.to_string_lossy().into_owned(),
                "--recipients-dir".to_string(),
                recipients.to_string_lossy().into_owned(),
            ])
            .unwrap(),
            0
        );
        assert_eq!(fs::read_to_string(output).unwrap(), "<title>Test</title>");
        assert!(!recipients.join(format!("{stem}.html")).exists());
        let _ = fs::remove_file(output);
        let _ = fs::remove_dir_all(base);
    }

    #[test]
    fn bulk_generation_propagates_output_write_failures() {
        let base =
            std::env::temp_dir().join(format!("simplewish-bulk-error-{}", std::process::id()));
        let recipients = base.join("recipients");
        let template = base.join("template.html");
        let stem = format!("bulk-write-error-{}", std::process::id());
        let name = format!("{stem}.html");
        fs::create_dir_all(&recipients).unwrap();
        fs::create_dir_all(&name).unwrap();
        fs::write(&template, "<title>Old</title>").unwrap();
        fs::write(
            recipients.join(format!("{stem}.json")),
            r#"{"title":"Test"}"#,
        )
        .unwrap();
        assert!(
            super::generate_cli(&[
                "--bulk".to_string(),
                "--template".to_string(),
                template.to_string_lossy().into_owned(),
                "--recipients-dir".to_string(),
                recipients.to_string_lossy().into_owned(),
            ])
            .is_err()
        );
        let _ = fs::remove_dir(name);
        let _ = fs::remove_dir_all(base);
    }

    #[test]
    fn generate_recipient_rejects_invalid_options_before_writing() {
        let base =
            std::env::temp_dir().join(format!("simplewish-invalid-cli-{}", std::process::id()));
        let data = base.with_extension("json");
        let output = PathBuf::from(format!(
            "{}.html",
            base.file_stem().and_then(|stem| stem.to_str()).unwrap()
        ));
        fs::write(&data, r#"{"title":"Test"}"#).unwrap();
        fs::write(&output, "preserve this file").unwrap();

        assert!(
            super::generate_cli(&[
                "--data".to_string(),
                data.to_string_lossy().into_owned(),
                "--otu".to_string(),
                "preview.html".to_string(),
            ])
            .is_err()
        );
        assert_eq!(fs::read_to_string(&output).unwrap(), "preserve this file");
        assert!(
            super::generate_cli(&[
                "--data".to_string(),
                data.to_string_lossy().into_owned(),
                "--out".to_string(),
            ])
            .is_err()
        );
        let _ = fs::remove_file(data);
        let _ = fs::remove_file(output);
    }
}
