use serde_json::Value;
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
    let Some(start) = text.find(variable) else {
        return;
    };
    let value_start = start + variable.len();
    let Some(relative_end) = text[value_start..].find(';') else {
        return;
    };
    text.replace_range(value_start..value_start + relative_end, value);
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
        if let Some(value) = json_field(data, field).filter(|value| !value.is_null() && !string_value(value).is_empty()) {
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
    if !meta.is_empty() {
        if let Some(start) = rendered.find("<!-- QR metadata:") {
            if let Some(relative_end) = rendered[start..].find("-->") {
                let end = start + relative_end + 3;
                rendered.insert_str(end, &format!("\n  {}", meta.join("\n  ")));
            }
        }
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
                .filter(|href| !href.is_null() && !string_value(href).is_empty())
            {
                list.push_str(&format!(
                    "          <li><a href=\"{}\" target=\"_blank\" rel=\"noopener\">{safe_text}</a></li>\n",
                    html_escape(&string_value(href), true)
                ));
            } else {
                list.push_str(&format!("          <li>{safe_text}</li>\n"));
            }
        }
        if let Some(start) = rendered.find("<ul id=\"gift-list\"") {
            if let Some(tag_end_relative) = rendered[start..].find('>') {
                let content_start = start + tag_end_relative + 1;
                if let Some(end) = rendered[content_start..].find("</ul>") {
                    let content_end = content_start + end;
                    rendered.replace_range(
                        content_start..content_end,
                        &format!("\n{list}        "),
                    );
                }
            }
        }
    }
    if let Some(notes) = json_field(data, "notes") {
        if let Some(section) = rendered.find("<section class=\"notes\">") {
            if let Some(start_relative) = rendered[section..].find("<p>") {
                let start = section + start_relative + 3;
                if let Some(end_relative) = rendered[start..].find("</p>") {
                    let end = start + end_relative;
                    rendered.replace_range(
                        start..end,
                        &html_escape(&string_value(notes), true),
                    );
                }
            }
        }
    }
    if let Some(start) = rendered.find(crate::MARKER_START) {
        if let Some(relative_end) = rendered[start + crate::MARKER_START.len()..].find(crate::MARKER_END) {
            let content_start = start + crate::MARKER_START.len();
            let content_end = content_start + relative_end;
            rendered.replace_range(content_start..content_end, "\n");
        }
    }
    rendered
}

fn render_file(
    template: &str,
    data_path: &Path,
    output: Option<&Path>,
) -> Result<PathBuf, String> {
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
    let template_path = PathBuf::from(super::qr::value_after(args, "--template", "index.html")?);
    let template = fs::read_to_string(&template_path)?;
    let bulk = args.iter().any(|arg| arg == "--bulk");
    if bulk {
        let recipients_dir = PathBuf::from(super::qr::value_after(args, "--recipients-dir", "recipients")?);
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
            .filter(|path| path.extension().is_some_and(|extension| extension == "json"))
            .collect::<Vec<_>>();
        data_files.sort();
        if data_files.is_empty() {
            println!("No recipient JSON files found to generate");
            return Ok(0);
        }
        for data_path in data_files {
            let filename = data_path.with_extension("html");
            if let Err(error) = render_file(&template, &data_path, Some(&filename)) {
                eprintln!("Failed to render {}: {error}", data_path.display());
            }
        }
        return Ok(0);
    }
    let Some(data_arg) = args.iter().position(|arg| arg == "--data") else {
        return Err(std::io::Error::other("--data is required unless --bulk is specified").into());
    };
    let data_path = PathBuf::from(
        args.get(data_arg + 1)
            .ok_or_else(|| std::io::Error::other("--data requires a file path"))?,
    );
    let output = args
        .iter()
        .position(|arg| arg == "--out")
        .map(|index| {
            args.get(index + 1)
                .map(Path::new)
                .ok_or_else(|| std::io::Error::other("--out requires a file path"))
        })
        .transpose()?;
    render_file(&template, &data_path, output)?;
    Ok(0)
}

#[cfg(test)]
mod tests {
    use super::render_from_template;
    use serde_json::json;

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
            "qr_foreground":"#abc123"
        });
        let html = render_from_template(template, &data);
        assert!(html.contains("<title>Elsa&#x27;s List</title>"));
        assert!(html.contains("Christmas List for Elsa &amp; Friends"));
        assert!(html.contains("A &lt;gift&gt;"));
        assert!(html.contains("a=1&amp;b=2"));
        assert!(html.contains("name=\"qr-foreground-color\""));
        assert!(html.contains("<!-- QR-PLACEHOLDER-START -->\n<!-- QR-PLACEHOLDER-END -->"));
    }
}
