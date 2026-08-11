import argparse
import html.parser
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple


CANONICAL_URL = 'https://valenfer.github.io/astroaida/'

REQUIRED_FILES = [
    'index.html',
    'styles.css',
    'moon-renderer.js',
    'main.js',
    'assets/favicon.svg',
]

DATA_FILES = ['apod.json', 'sky-today.json', 'moon.json', 'star-chart.json', 'near-earth.json']
DATA_META_FIELDS = ('source', 'fetched_at', 'status')
DATA_REQUIRED_FIELDS = {
    'moon.json': ('image_url', 'phase', 'illumination', 'distance_km'),
}
ALLOWED_STATUSES = ('preview', 'live')

UNSAFE_SCHEMES = ('javascript:', 'file:', 'data:')

SECRET_PATTERNS = [
    re.compile(r'api[_-]?key\s*=\s*[A-Za-z0-9_\-]{8,}', re.IGNORECASE),
    re.compile(r'api[_-]?secret\s*[:=]\s*\S+', re.IGNORECASE),
    re.compile(r'BEGIN (RSA |EC |DSA )?PRIVATE KEY'),
    re.compile(r'\bNASA_API_KEY\s*[:=]\s*\S'),
    re.compile(r'\bASTRONOMY_APP_(ID|SECRET)\s*[:=]\s*\S'),
    re.compile(r'password\s*[:=]\s*\S+', re.IGNORECASE),
    re.compile(r'token\s*[:=]\s*[A-Za-z0-9_\-]{8,}', re.IGNORECASE),
]

LOCAL_PATH_PATTERNS = [
    re.compile(r'(?<![A-Za-z0-9])[a-zA-Z]:[\\/]'),
    re.compile(r'file://'),
    re.compile(r'[/\\](?:Users|home)[/\\]'),
]

DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scan_for_secrets(relpath: str, text: str) -> List[str]:
    errors = []
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append('{}: possible secret leak matching {}'.format(relpath, pattern.pattern))
            break
    return errors


def check_local_path_leak(relpath: str, text: str) -> List[str]:
    errors = []
    for pattern in LOCAL_PATH_PATTERNS:
        if pattern.search(text):
            errors.append('{}: local path leak matching {}'.format(relpath, pattern.pattern))
            break
    return errors


def check_url(relpath: str, url: str) -> List[str]:
    lowered = url.strip().lower()
    if lowered.startswith(UNSAFE_SCHEMES):
        return ['{}: unsafe URL scheme: {!r}'.format(relpath, url)]
    return []


def find_urls(data: object) -> List[str]:
    urls = []
    if isinstance(data, dict):
        for key, value in data.items():
            if 'url' in key.lower() and isinstance(value, str):
                urls.append(value)
            urls.extend(find_urls(value))
    elif isinstance(data, list):
        for item in data:
            urls.extend(find_urls(item))
    return urls


def validate_data_file(root: str, relpath: str) -> List[str]:
    errors = []
    relpath = relpath.replace(os.sep, '/')
    path = os.path.join(root, relpath)
    if not os.path.exists(path):
        return ['missing required file: {}'.format(relpath)]
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except OSError as exc:
        return ['cannot read {}: {}'.format(relpath, exc)]

    errors.extend(scan_for_secrets(relpath, text))
    errors.extend(check_local_path_leak(relpath, text))

    try:
        data = json.loads(text)
    except ValueError:
        return errors + ['{}: invalid JSON'.format(relpath)]

    for field in DATA_META_FIELDS:
        if field not in data or data.get(field) in (None, ''):
            errors.append('{}: missing required field {}'.format(relpath, field))

    status = data.get('status')
    if status not in ALLOWED_STATUSES:
        errors.append('{}: invalid status {!r} (allowed: {})'.format(
            relpath, status, ', '.join(ALLOWED_STATUSES)))

    required_fields = DATA_REQUIRED_FIELDS.get(relpath.split('/')[-1], ())
    for field in required_fields:
        if field not in data or data.get(field) in (None, ''):
            errors.append('{}: missing required field {}'.format(relpath, field))

    for url in find_urls(data):
        errors.extend(check_url(relpath, url))

    return errors


class SiteParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: List[Tuple[str, str, str]] = []
        self.assets: List[str] = []
        self.scripts: List[str] = []
        self.canonical: Optional[str] = None
        self.meta_description: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        values = {key: (value or '') for key, value in attrs}
        if tag == 'a':
            href = values.get('href')
            if href:
                self.links.append((href, values.get('target', ''), values.get('rel', '')))
        elif tag == 'link':
            href = values.get('href')
            if href:
                if values.get('rel') == 'canonical':
                    self.canonical = href
                else:
                    self.assets.append(href)
        elif tag == 'script':
            src = values.get('src')
            if src:
                self.scripts.append(src)
                self.assets.append(src)
        elif tag in ('img', 'video', 'iframe', 'audio', 'source'):
            src = values.get('src')
            if src:
                self.assets.append(src)
        elif tag == 'meta':
            name = values.get('name', '').lower()
            content = values.get('content', '')
            if name == 'description' and content:
                self.meta_description = content


def _is_external(url: str) -> bool:
    return url.startswith(('http://', 'https://', '//'))


def _resolve_local(url: str) -> Optional[str]:
    path = url.split('#')[0].split('?')[0]
    if not path:
        return None
    return path


def validate_html(root: str) -> List[str]:
    errors = []
    html_path = os.path.join(root, 'index.html')
    if not os.path.exists(html_path):
        return ['missing required file: index.html']
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except OSError as exc:
        return ['cannot read index.html: {}'.format(exc)]

    errors.extend(scan_for_secrets('index.html', text))
    errors.extend(check_local_path_leak('index.html', text))

    parser = SiteParser()
    try:
        parser.feed(text)
    except Exception as exc:
        return errors + ['index.html: parse error: {}'.format(exc)]

    if not parser.meta_description:
        errors.append('index.html: missing meta description')

    if parser.canonical != CANONICAL_URL:
        errors.append('index.html: canonical must be {!r}, got {!r}'.format(
            CANONICAL_URL, parser.canonical))

    for url, target, rel in parser.links:
        errors.extend(check_url('index.html', url))
        if url in ('', '#') or url.lower().startswith('javascript:'):
            errors.append('index.html: empty/dead link href={!r}'.format(url))
            continue
        if url.startswith('#'):
            continue
        if url.lower().startswith('mailto:'):
            continue
        if target == '_blank' and 'noopener' not in (rel or '').lower():
            errors.append('index.html: _blank link missing rel=noopener: {!r}'.format(url))
        if _is_external(url):
            continue
        if url.startswith('/'):
            errors.append('index.html: root-relative link {!r} (site lives under /astroaida/)'.format(url))
            continue
        local = _resolve_local(url)
        if local and not os.path.exists(os.path.join(root, local)):
            errors.append('index.html: missing local link target {!r}'.format(url))

    for asset in parser.assets:
        errors.extend(check_url('index.html', asset))
        if _is_external(asset):
            continue
        if asset.startswith('/'):
            errors.append('index.html: root-relative asset {!r} (site lives under /astroaida/)'.format(asset))
            continue
        local = _resolve_local(asset)
        if local and not os.path.exists(os.path.join(root, local)):
            errors.append('index.html: missing asset {!r}'.format(asset))

    if 'moon-renderer.js' not in parser.scripts:
        errors.append('index.html: missing moon-renderer.js script')
    elif 'main.js' not in parser.scripts:
        errors.append('index.html: missing main.js script')
    elif parser.scripts.index('moon-renderer.js') >= parser.scripts.index('main.js'):
        errors.append('index.html: moon-renderer.js must load before main.js')

    return errors


def validate_site(root: str) -> List[str]:
    errors = []
    for rel in REQUIRED_FILES:
        if not os.path.exists(os.path.join(root, rel)):
            errors.append('missing required file: {}'.format(rel))

    for name in DATA_FILES:
        errors.extend(validate_data_file(root, os.path.join('data', name)))

    errors.extend(validate_html(root))

    for rel in ('styles.css', 'moon-renderer.js', 'main.js'):
        path = os.path.join(root, rel)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except OSError as exc:
                errors.append('cannot read {}: {}'.format(rel, exc))
                continue
            errors.extend(scan_for_secrets(rel, text))
            errors.extend(check_local_path_leak(rel, text))

    return errors


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog='validate_site',
        description='Validate the static AstroAIDA site and its datasets.')
    parser.add_argument('root', nargs='?', default=DEFAULT_ROOT,
                        help='Site root directory to validate (default: astroaida/).')
    args = parser.parse_args(argv)

    errors = validate_site(args.root)
    for error in errors:
        print('ERROR: {}'.format(error))
    if errors:
        print('AstroAIDA validation FAILED with {} error(s).'.format(len(errors)))
        return 1
    print('AstroAIDA validation OK.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
