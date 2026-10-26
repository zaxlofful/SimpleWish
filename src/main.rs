use std::env;
use std::process::ExitCode;

fn main() -> ExitCode {
    match run(env::args().skip(1).collect()) {
        Ok(code) => ExitCode::from(code),
        Err(error) => {
            eprintln!("Error: {error}");
            ExitCode::from(2)
        }
    }
}

fn run(args: Vec<String>) -> Result<u8, Box<dyn std::error::Error>> {
    let Some(command) = args.first().map(String::as_str) else {
        print_help();
        return Ok(0);
    };
    match command {
        "generate-qr" => simplewish::qr::generate_cli(&args[1..]),
        "inject-qr" => simplewish::qr::inject_cli(&args[1..]),
        "generate-recipient" => simplewish::recipient::generate_cli(&args[1..]),
        "check-svg" => simplewish::qr::check_svg_cli(&args[1..]),
        "check-todo" => simplewish::automation::check_todo_cli(&args[1..]),
        "update-todo-from-prs" => simplewish::automation::update_todo_cli(&args[1..]),
        "render-readme" => simplewish::automation::render_readme_cli(),
        "regenerate-reference" => simplewish::qr::regenerate_reference_cli(),
        "help" | "--help" | "-h" => {
            print_help();
            Ok(0)
        }
        other => Err(std::io::Error::other(format!(
            "unknown command `{other}`; use `simplewish help`"
        ))
        .into()),
    }
}

fn print_help() {
    println!(
        "SimpleWish tools\n\
         \n\
         Commands:\n\
           generate-qr          Generate QR SVG files\n\
           inject-qr            Inject SVGs between HTML markers\n\
           generate-recipient   Render recipient JSON into HTML\n\
           check-svg            Check generated decoration fragments\n\
           check-todo           Return nonzero when TODO.md has content\n\
           update-todo-from-prs Remove TODOs completed in merged PRs\n\
           render-readme        Fix README badge links\n\
           regenerate-reference Regenerate QR SVG reference files"
    );
}
