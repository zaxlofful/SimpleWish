use std::process::Command;

#[test]
fn check_commands_show_help_without_checking_files() {
    let directory = std::env::temp_dir().join(format!("simplewish-help-{}", std::process::id()));
    std::fs::create_dir_all(&directory).unwrap();
    std::fs::write(directory.join("TODO.md"), "Pending task").unwrap();
    for command in ["check-todo", "check-svg"] {
        for flag in ["--help", "-h"] {
            let output = Command::new(env!("CARGO_BIN_EXE_simplewish"))
                .args([command, flag])
                .current_dir(&directory)
                .output()
                .unwrap();
            assert!(output.status.success(), "{command} {flag}: {output:?}");
            assert!(
                String::from_utf8(output.stdout)
                    .unwrap()
                    .contains("Commands:")
            );
        }
    }
    std::fs::remove_dir_all(directory).unwrap();
}
