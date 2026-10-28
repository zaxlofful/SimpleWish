use serde_json::Value;
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

pub fn is_todo_empty(path: &Path) -> bool {
    match fs::read_to_string(path) {
        Ok(content) => content.trim().is_empty(),
        Err(error) => {
            eprintln!(
                "TODO.md not found or unreadable at {}: {error}",
                path.display()
            );
            true
        }
    }
}

pub fn check_todo_cli(_args: &[String]) -> Result<u8, Box<dyn std::error::Error>> {
    if is_todo_empty(Path::new("TODO.md")) {
        println!("TODO.md is empty or blank");
        Ok(0)
    } else {
        println!("TODO.md contains content");
        Ok(1)
    }
}

pub fn extract_completed_items(body: Option<&str>) -> Vec<String> {
    let Some(body) = body else {
        return Vec::new();
    };
    let mut completed = Vec::new();
    for line in body.lines() {
        let trimmed = line.trim();
        for prefix in ["fixed:", "completed:", "done:", "resolved:"] {
            if let Some(index) = trimmed.to_ascii_lowercase().find(prefix) {
                let item = trimmed[index + prefix.len()..].trim();
                if !item.is_empty() {
                    completed.push(item.to_string());
                }
            }
        }
        let lower = trimmed.to_ascii_lowercase();
        for (index, _) in lower.match_indices('-') {
            let after_marker = &lower[index + 1..];
            let whitespace =
                after_marker.len() - after_marker.trim_start_matches([' ', '\t']).len();
            if whitespace > 0 && after_marker[whitespace..].starts_with("[x]") {
                let item = trimmed[index + 1 + whitespace + 3..].trim();
                if !item.is_empty() {
                    completed.push(item.to_string());
                }
                break;
            }
        }
    }
    completed
}

fn normalize_todo_line(line: &str) -> String {
    let trimmed = line.trim();
    let mut chars = trimmed.char_indices().peekable();
    let mut prefix_end = 0;
    if matches!(chars.peek().map(|(_, ch)| *ch), Some('-' | '*' | '+')) {
        prefix_end = chars.next().map_or(0, |(index, ch)| index + ch.len_utf8());
        while matches!(chars.peek().map(|(_, ch)| *ch), Some(' ' | '\t')) {
            prefix_end = chars
                .next()
                .map_or(prefix_end, |(index, ch)| index + ch.len_utf8());
        }
    } else {
        let start = prefix_end;
        while matches!(chars.peek().map(|(_, ch)| *ch), Some(ch) if ch.is_ascii_digit()) {
            prefix_end = chars
                .next()
                .map_or(prefix_end, |(index, ch)| index + ch.len_utf8());
        }
        if prefix_end > start && matches!(chars.peek().map(|(_, ch)| *ch), Some('.')) {
            prefix_end = chars
                .next()
                .map_or(prefix_end, |(index, ch)| index + ch.len_utf8());
            while matches!(chars.peek().map(|(_, ch)| *ch), Some(' ' | '\t')) {
                prefix_end = chars
                    .next()
                    .map_or(prefix_end, |(index, ch)| index + ch.len_utf8());
            }
        } else {
            prefix_end = 0;
        }
    }
    let remaining = trimmed[prefix_end..].trim_start();
    let remaining = if remaining.starts_with("[x]") || remaining.starts_with("[ ]") {
        remaining[3..].trim_start()
    } else {
        remaining
    };
    remaining.to_lowercase()
}

fn words(value: &str) -> HashSet<String> {
    value.split_whitespace().map(str::to_lowercase).collect()
}

pub fn update_todo_file(path: &Path, completed: &[String]) -> Result<bool, String> {
    let content = match fs::read_to_string(path) {
        Ok(content) => content,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            println!("TODO.md not found");
            return Ok(false);
        }
        Err(error) => return Err(format!("cannot read {}: {error}", path.display())),
    };
    if completed.is_empty() {
        println!("No completed items to remove");
        return Ok(false);
    }
    let completed = completed
        .iter()
        .map(|item| {
            let normalized = item.trim().to_lowercase();
            (normalized.clone(), words(&normalized))
        })
        .collect::<Vec<_>>();
    let mut removed = 0;
    let mut lines = Vec::new();
    for line in content.lines() {
        let normalized = normalize_todo_line(line);
        if normalized.is_empty() {
            lines.push(line.to_string());
            continue;
        }
        let normalized_words = words(&normalized);
        let matched = completed.iter().any(|(full, item_words)| {
            normalized == *full
                || (!item_words.is_empty()
                    && item_words
                        .iter()
                        .all(|word| normalized_words.contains(word.as_str())))
        });
        if matched {
            println!("Removing completed item: {}", line.trim());
            removed += 1;
        } else {
            lines.push(line.to_string());
        }
    }
    if removed == 0 {
        println!("No matching TODO items found to remove");
        return Ok(false);
    }
    let mut result = lines.join("\n");
    while result.contains("\n\n\n") {
        result = result.replace("\n\n\n", "\n\n");
    }
    result = result.trim().to_string();
    if !result.is_empty() {
        result.push('\n');
    }
    fs::write(path, result)
        .map_err(|error| format!("cannot update {}: {error}", path.display()))?;
    println!("Removed {removed} completed item(s) from TODO.md");
    Ok(true)
}

fn merged_prs() -> Result<Vec<Value>, String> {
    let output = Command::new("gh")
        .args([
            "pr",
            "list",
            "--state",
            "merged",
            "--label",
            "todo-automation",
            "--json",
            "number,title,body,mergedAt",
            "--limit",
            "10",
        ])
        .output()
        .map_err(|error| format!("cannot run gh: {error}"))?;
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).trim().to_string());
    }
    serde_json::from_slice(&output.stdout).map_err(|error| format!("invalid gh JSON: {error}"))
}

pub fn update_todo_cli(_args: &[String]) -> Result<u8, Box<dyn std::error::Error>> {
    println!("Fetching merged PRs with todo-automation label...");
    let prs = match merged_prs() {
        Ok(prs) => prs,
        Err(error) => {
            eprintln!("Error fetching merged PRs: {error}");
            return Ok(0);
        }
    };
    if prs.is_empty() {
        println!("No merged TODO automation PRs found");
        return Ok(0);
    }
    println!("Found {} merged PR(s)", prs.len());
    let mut completed = Vec::new();
    for pr in &prs {
        println!(
            "Processing PR #{}: {}",
            pr.get("number").unwrap_or(&Value::Null),
            pr.get("title").and_then(Value::as_str).unwrap_or("")
        );
        let items = extract_completed_items(pr.get("body").and_then(Value::as_str));
        if !items.is_empty() {
            println!("  Found {} completed item(s)", items.len());
            completed.extend(items);
        }
    }
    if !completed.is_empty() {
        println!("\nTotal completed items to remove: {}", completed.len());
        if update_todo_file(Path::new("TODO.md"), &completed).map_err(std::io::Error::other)? {
            println!("\nTODO.md has been updated");
        } else {
            println!("\nTODO.md was not modified");
        }
    } else {
        println!("\nNo completed items found in merged PRs");
    }
    Ok(0)
}

fn owner_repo() -> (String, String) {
    if let Ok(repository) = std::env::var("GITHUB_REPOSITORY")
        && let Some((owner, repo)) = repository.split_once('/')
    {
        return (owner.to_string(), repo.to_string());
    }
    if let Ok(output) = Command::new("git")
        .args(["remote", "get-url", "origin"])
        .output()
        && output.status.success()
        && let Some((owner, repo)) =
            parse_github_repository(String::from_utf8_lossy(&output.stdout).trim())
    {
        return (owner, repo);
    }
    ("ZaxLofful".to_string(), "SimpleWish".to_string())
}

fn parse_github_repository(url: &str) -> Option<(String, String)> {
    let stripped = url.trim_end_matches(".git");
    let github = stripped.find("github.com")?;
    let path = &stripped[github + "github.com".len()..];
    let parts = path
        .trim_start_matches([':', '/'])
        .split('/')
        .collect::<Vec<_>>();
    (parts.len() >= 2 && !parts[0].is_empty() && !parts[1].is_empty())
        .then(|| (parts[0].to_string(), parts[1].to_string()))
}

fn image_bounds(text: &str, start: usize) -> Option<(usize, usize, String)> {
    let rest = text.get(start..)?;
    if !rest.starts_with("![") {
        return None;
    }
    let label_end = rest.find("](")?;
    let url_end = rest[label_end + 2..].find(')')? + label_end + 2;
    Some((
        start,
        start + url_end + 1,
        rest[label_end + 2..url_end].trim().to_string(),
    ))
}

fn workflow_link(owner: &str, repo: &str, filename: &str) -> Option<String> {
    let workflows = Path::new(".github/workflows");
    let candidate = filename.to_string();
    if workflows.join(&candidate).is_file() {
        return Some(format!(
            "https://github.com/{owner}/{repo}/actions/workflows/{candidate}"
        ));
    }
    let stem = Path::new(filename).file_stem()?.to_str()?.to_lowercase();
    let entries = fs::read_dir(workflows).ok()?;
    for entry in entries.flatten() {
        let path = entry.path();
        let name = path.file_name()?.to_str()?.to_string();
        if let Ok(contents) = fs::read_to_string(&path) {
            for line in contents.lines() {
                let Some((key, value)) = line.trim().split_once(':') else {
                    continue;
                };
                if key.eq_ignore_ascii_case("name")
                    && value
                        .trim()
                        .trim_matches(['\'', '"'])
                        .eq_ignore_ascii_case(&stem)
                {
                    return Some(format!(
                        "https://github.com/{owner}/{repo}/actions/workflows/{name}"
                    ));
                }
            }
        }
    }
    None
}

fn canonical_image_link(image_url: &str, owner: &str, repo: &str, repo_url: &str) -> String {
    if image_url.contains("github.com")
        && image_url.contains("/actions/workflows/")
        && parse_github_repository(image_url).is_some_and(|(image_owner, image_repo)| {
            image_owner.eq_ignore_ascii_case(owner) && image_repo.eq_ignore_ascii_case(repo)
        })
        && let Some((_, tail)) = image_url.split_once("/actions/workflows/")
    {
        let filename = tail.split('/').next().unwrap_or_default();
        if let Some(url) = workflow_link(owner, repo, filename) {
            return url;
        }
        return image_url
            .replace("/badge.svg", "")
            .split('?')
            .next()
            .unwrap_or(image_url)
            .to_string();
    }
    repo_url.to_string()
}

fn rewrite_readme_links(content: &str, owner: &str, repo: &str) -> (String, usize) {
    let repo_url = format!("https://github.com/{owner}/{repo}");
    let mut changes = 0;
    let mut output = String::new();
    for line in content.lines() {
        let mut rewritten = String::new();
        let mut cursor = 0;
        while let Some(start) = line[cursor..].find("![").map(|offset| cursor + offset) {
            let Some((start, end, image_url)) = image_bounds(line, start) else {
                rewritten.push_str(&line[cursor..start + 2]);
                cursor = start + 2;
                continue;
            };
            let linked =
                start > 0 && line.as_bytes()[start - 1] == b'[' && line[end..].starts_with("](");
            let image_prefix_start = if linked { start - 1 } else { start };
            rewritten.push_str(&line[cursor..image_prefix_start]);
            if linked {
                let link_start = end + 2;
                if let Some(link_end_relative) = line[link_start..].find(')') {
                    let link_end = link_start + link_end_relative;
                    let current_link = &line[link_start..link_end];
                    let parsed = parse_github_repository(current_link.trim());
                    let target = if image_url.contains("/actions/workflows/")
                        && parse_github_repository(&image_url).is_some_and(
                            |(image_owner, image_repo)| {
                                image_owner.eq_ignore_ascii_case(owner)
                                    && image_repo.eq_ignore_ascii_case(repo)
                            },
                        ) {
                        Some(canonical_image_link(&image_url, owner, repo, &repo_url))
                    } else if parsed.is_some_and(|(link_owner, link_repo)| {
                        !(link_owner.eq_ignore_ascii_case(owner)
                            && link_repo.eq_ignore_ascii_case(repo))
                    }) {
                        Some(repo_url.clone())
                    } else {
                        None
                    };
                    rewritten.push_str(&line[image_prefix_start..link_start]);
                    if let Some(target) = target {
                        if current_link.trim() != target {
                            changes += 1;
                        }
                        rewritten.push_str(&target);
                    } else {
                        rewritten.push_str(current_link);
                    }
                    rewritten.push(')');
                    cursor = link_end + 1;
                    continue;
                }
            }
            let target = canonical_image_link(&image_url, owner, repo, &repo_url);
            rewritten.push('[');
            rewritten.push_str(&line[start..end]);
            rewritten.push_str("](");
            rewritten.push_str(&target);
            rewritten.push(')');
            changes += 1;
            cursor = end;
        }
        rewritten.push_str(&line[cursor..]);
        output.push_str(&rewritten);
        output.push('\n');
    }
    if !content.ends_with('\n') {
        output.pop();
    }
    (output, changes)
}

pub fn render_readme_cli() -> Result<u8, Box<dyn std::error::Error>> {
    let output = PathBuf::from("README.md");
    if !output.exists() {
        println!("README.md not found; nothing to do");
        return Ok(0);
    }
    let (owner, repo) = owner_repo();
    let content = fs::read_to_string(&output)?;
    let (updated, changes) = rewrite_readme_links(&content, &owner, &repo);
    if changes > 0 {
        fs::write(&output, updated)?;
        println!(
            "Fixed or wrapped {changes} badge(s) to point to https://github.com/{owner}/{repo} in README.md"
        );
    } else {
        println!("No badge link changes required");
    }
    Ok(0)
}

#[cfg(test)]
mod tests {
    use super::{extract_completed_items, is_todo_empty, update_todo_file};
    use std::fs;

    #[test]
    fn todo_empty_check_handles_empty_whitespace_and_content() {
        let path = std::env::temp_dir().join(format!("simplewish-todo-{}.md", std::process::id()));
        fs::write(&path, " \n\t").unwrap();
        assert!(is_todo_empty(&path));
        fs::write(&path, "1. Add support").unwrap();
        assert!(!is_todo_empty(&path));
        let _ = fs::remove_file(path);
    }

    #[test]
    fn extracts_completed_lines_and_checkboxes() {
        let body = "Fixed: Add styling\nCOMPLETED: Review output\nDone: Handle cases\n\
            Resolved: Update docs\n- [x] Finish tests\n- [X] Also finished\n\
            -   [x] Extra spaces\n-\t[X] Tab spacing\n- [ ] Pending\nDone:";
        let completed = extract_completed_items(Some(body));
        assert_eq!(
            completed,
            [
                "Add styling",
                "Review output",
                "Handle cases",
                "Update docs",
                "Finish tests",
                "Also finished",
                "Extra spaces",
                "Tab spacing"
            ]
        );
        assert!(extract_completed_items(None).is_empty());
    }

    #[test]
    fn todo_update_removes_matching_items_and_preserves_unmatched_content() {
        let path =
            std::env::temp_dir().join(format!("simplewish-update-{}.md", std::process::id()));
        fs::write(
            &path,
            "  1. Coloring by CSS  \n- [ ] Finish tests\n+ Keep this task\n\n",
        )
        .unwrap();
        assert!(
            update_todo_file(
                &path,
                &["  coloring by css ".to_string(), "Finish tests".to_string()]
            )
            .unwrap()
        );
        let output = fs::read_to_string(&path).unwrap();
        assert!(!output.contains("Coloring by CSS"));
        assert!(!output.contains("Finish tests"));
        assert_eq!(output, "+ Keep this task\n");
        let _ = fs::remove_file(path);
    }

    #[test]
    fn todo_update_leaves_file_unchanged_without_a_match() {
        let path =
            std::env::temp_dir().join(format!("simplewish-update-none-{}.md", std::process::id()));
        let original = "1. Keep this task\n";
        fs::write(&path, original).unwrap();
        assert!(!update_todo_file(&path, &["Different task".to_string()]).unwrap());
        assert_eq!(fs::read_to_string(&path).unwrap(), original);
        assert!(!update_todo_file(&path, &[]).unwrap());
        assert_eq!(fs::read_to_string(&path).unwrap(), original);
        let _ = fs::remove_file(path);
    }

    #[test]
    fn todo_update_matches_mixed_case_completion_subsets() {
        let path =
            std::env::temp_dir().join(format!("simplewish-update-case-{}.md", std::process::id()));
        fs::write(&path, "1. Add coloring by CSS\n").unwrap();
        assert!(update_todo_file(&path, &["Coloring by CSS".to_string()]).unwrap());
        assert_eq!(fs::read_to_string(&path).unwrap(), "");
        let _ = fs::remove_file(path);
    }

    #[test]
    fn todo_update_matches_non_ascii_mixed_case_completions() {
        let path = std::env::temp_dir().join(format!(
            "simplewish-update-unicode-{}.md",
            std::process::id()
        ));
        fs::write(&path, "1. Éclairage\n").unwrap();
        assert!(update_todo_file(&path, &["éclairage".to_string()]).unwrap());
        assert_eq!(fs::read_to_string(&path).unwrap(), "");
        let _ = fs::remove_file(path);
    }

    #[test]
    fn normalizes_list_prefixes_and_checkboxes_before_matching() {
        assert_eq!(
            super::normalize_todo_line("  - [x] Add Feature  "),
            "add feature"
        );
        assert_eq!(
            super::normalize_todo_line("* [ ] Add Feature"),
            "add feature"
        );
        assert_eq!(super::normalize_todo_line("+ Add Feature"), "add feature");
        assert_eq!(
            super::normalize_todo_line("12.\tAdd Feature"),
            "add feature"
        );
        assert_eq!(super::normalize_todo_line("  Plain text  "), "plain text");
        assert_eq!(super::normalize_todo_line("   "), "");
    }

    #[test]
    fn readme_badge_links_are_repaired() {
        let source = "![build](https://img.shields.io/x)\n\
            [![tests](https://github.com/owner/repo/actions/workflows/test.yml/badge.svg)](https://github.com/elsewhere/nope)\n";
        let (result, count) = super::rewrite_readme_links(source, "owner", "repo");
        assert_eq!(count, 2);
        assert_eq!(
            result,
            "[![build](https://img.shields.io/x)](https://github.com/owner/repo)\n\
             [![tests](https://github.com/owner/repo/actions/workflows/test.yml/badge.svg)](https://github.com/owner/repo/actions/workflows/test.yml)\n"
        );
    }

    #[test]
    fn readme_rewrites_multiple_badges_with_surrounding_markdown() {
        let source = "Before ![plain](https://img.shields.io/plain) after \
            [![tests](https://github.com/owner/repo/actions/workflows/test.yml/badge.svg)](https://github.com/elsewhere/nope) \
            and [![other](https://img.shields.io/other)](https://github.com/another/project) end \
            ![last](https://img.shields.io/last)";
        let (result, count) = super::rewrite_readme_links(source, "owner", "repo");
        assert_eq!(count, 4);
        assert_eq!(
            result,
            "Before [![plain](https://img.shields.io/plain)](https://github.com/owner/repo) after \
            [![tests](https://github.com/owner/repo/actions/workflows/test.yml/badge.svg)](https://github.com/owner/repo/actions/workflows/test.yml) \
            and [![other](https://img.shields.io/other)](https://github.com/owner/repo) end \
            [![last](https://img.shields.io/last)](https://github.com/owner/repo)"
        );
    }

    #[test]
    fn readme_rewrite_preserves_incomplete_image_syntax() {
        let source = "Before ![build](https://img.shields.io/build) after ![incomplete";
        let (result, count) = super::rewrite_readme_links(source, "owner", "repo");
        assert_eq!(count, 1);
        assert_eq!(
            result,
            "Before [![build](https://img.shields.io/build)](https://github.com/owner/repo) after ![incomplete"
        );
    }

    #[test]
    fn parses_github_repository_urls_and_rejects_non_github_urls() {
        assert_eq!(
            super::parse_github_repository("https://github.com/owner/repo"),
            Some(("owner".to_string(), "repo".to_string()))
        );
        assert_eq!(
            super::parse_github_repository("git@github.com:owner/repo.git"),
            Some(("owner".to_string(), "repo".to_string()))
        );
        assert_eq!(
            super::parse_github_repository("https://example.com/o/r"),
            None
        );
        assert_eq!(
            super::parse_github_repository("https://github.com/owner"),
            None
        );
    }

    #[test]
    fn extracts_image_bounds_without_consuming_trailing_markdown() {
        let image = "![build status](https://img.example/build.svg)";
        assert_eq!(
            super::image_bounds(image, 0),
            Some((0, image.len(), "https://img.example/build.svg".to_string()))
        );
        assert_eq!(
            super::image_bounds("prefix ![x](url) suffix", 7),
            Some((7, 16, "url".to_string()))
        );
        assert_eq!(super::image_bounds("not an image", 0), None);
        assert_eq!(super::image_bounds("![missing destination]", 0), None);
        assert_eq!(super::image_bounds("é![x](url)", 1), None);
    }
}
