import sys


def main():
    path = 'scripts/generated_qr/index.svg'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            s = f.read()
    except Exception as e:
        print('ERROR: cannot read', path, e)
        return 2

    checks = [
        ('star', 'points="100,54.11'),
        ('bow_left', 'M92,158'),
        ('bow_right', 'M108,158'),
        ('garland', 'M74,128'),
        ('ellipse', 'ellipse cx="92"'),
        ('gloss', 'circle cx="116"'),
    ]

    ok = True
    for name, pat in checks:
        found = pat in s
        print(f'{name}:', 'OK' if found else 'MISSING')
        if not found:
            ok = False

    return 0 if ok else 3


if __name__ == '__main__':
    raise SystemExit(main())
