from scripts.check_svg import main


def test_check_svg_all_present(tmp_path, monkeypatch):
    # create scripts/generated_qr and index.svg with expected fragments
    out_dir = tmp_path / 'scripts' / 'generated_qr'
    out_dir.mkdir(parents=True)
    svg_path = out_dir / 'index.svg'
    content = (
        '...points="100,54.11"...M92,158...M108,158...M74,128...ellipse cx="92"...circle cx="116"...'
    )
    svg_path.write_text(content, encoding='utf-8')

    # run from repo root => monkeypatch cwd
    monkeypatch.chdir(str(tmp_path))

    rc = main()
    assert rc == 0


def test_check_svg_missing_fragment(tmp_path, monkeypatch):
    out_dir = tmp_path / 'scripts' / 'generated_qr'
    out_dir.mkdir(parents=True)
    svg_path = out_dir / 'index.svg'
    # omit one required fragment
    content = '...points="100,54.11"...M92,158...M74,128...ellipse cx="92"...'
    svg_path.write_text(content, encoding='utf-8')

    monkeypatch.chdir(str(tmp_path))

    rc = main()
    assert rc != 0
