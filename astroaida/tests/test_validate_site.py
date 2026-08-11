import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from validate_site import validate_site, validate_data_file, validate_html


CANONICAL_URL = 'https://valenfer.github.io/astroaida/'


def valid_data(name):
    datasets = {
        'apod.json': {
            'source': 'NASA APOD', 'fetched_at': '2026-08-11T12:00:00+00:00', 'status': 'preview',
            'media_type': 'image', 'url': 'https://apod.nasa.gov/apod/image/2608/sample.jpg',
        },
        'sky-today.json': {
            'source': 'AstronomyAPI', 'fetched_at': '2026-08-11T12:00:00+00:00', 'status': 'preview',
            'bodies': [{'name': 'Mercury', 'altitude': 15.2, 'azimuth': 245.3}],
            'observer': {'latitude': 37.38283, 'longitude': -5.97317, 'elevation': 0, 'label': 'Sevilla'},
        },
        'moon.json': {
            'source': 'AstronomyAPI', 'fetched_at': '2026-08-11T12:00:00+00:00', 'status': 'preview',
            'phase': 'Gibosa creciente', 'illumination': 0.78, 'distance_km': 378500.0,
            'image_url': 'https://widgets.astronomyapi.com/moon-phase/generated/20260811.png',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317, 'elevation': 0, 'label': 'Sevilla'},
        },
        'star-chart.json': {
            'source': 'AstronomyAPI', 'fetched_at': '2026-08-11T12:00:00+00:00', 'status': 'preview',
            'image_url': 'https://api.astronomyapi.com/api/v2/studio/star-chart/sample.png',
            'style': 'inverted',
        },
        'near-earth.json': {
            'source': 'NASA NeoWs', 'fetched_at': '2026-08-11T12:00:00+00:00', 'status': 'preview',
            'asteroids': [{
                'date': '2026-08-11', 'name': '(2026 XYZ1)',
                'estimated_diameter_km': {'min': 0.1, 'max': 0.2},
                'miss_distance_km': 4000000, 'velocity_km_s': 18.2, 'hazardous': False,
                'nasa_url': 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#obj=1',
            }],
        },
    }
    return datasets[name]


VALID_HTML = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>AstroAIDA</title>
<meta name="description" content="Observación astronómica desde Sevilla.">
<meta property="og:title" content="AstroAIDA">
<link rel="canonical" href="https://valenfer.github.io/astroaida/">
<link rel="stylesheet" href="styles.css">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
</head>
<body>
<a class="skip" href="#contenido">Saltar al contenido</a>
<main id="contenido"><h1>AstroAIDA</h1></main>
<script src="moon-renderer.js"></script>
<script src="main.js"></script>
</body>
</html>
"""


class TestValidateSite(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def write_json(self, rel, data):
        self.write(rel, json.dumps(data))

    def build_valid_site(self):
        self.write('index.html', VALID_HTML)
        self.write('styles.css', 'body { color: #e8e6df; }')
        self.write('moon-renderer.js', "'use strict';\nconst MOON = {};\n")
        self.write('main.js', "'use strict';\nconst DATA = 'data/';\n")
        self.write('assets/favicon.svg', '<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        for name in ('apod.json', 'sky-today.json', 'moon.json', 'star-chart.json', 'near-earth.json'):
            self.write_json(os.path.join('data', name), valid_data(name))

    def test_missing_required_files(self):
        errors = validate_site(self.root)
        self.assertTrue(any('index.html' in e for e in errors))
        self.assertTrue(any('styles.css' in e for e in errors))
        self.assertTrue(any('moon-renderer.js' in e for e in errors))
        self.assertTrue(any('assets/favicon.svg' in e for e in errors))
        self.assertTrue(any('data/apod.json' in e for e in errors))

    def test_invalid_json(self):
        self.write_json(os.path.join('data', 'apod.json'), valid_data('apod.json'))
        self.write('data/sky-today.json', 'not json at all')
        errors = validate_site(self.root)
        self.assertTrue(any('sky-today.json' in e and 'JSON' in e for e in errors))

    def test_missing_meta_fields(self):
        data = valid_data('apod.json')
        del data['status']
        self.write_json(os.path.join('data', 'apod.json'), data)
        errors = validate_site(self.root)
        self.assertTrue(any('apod.json' in e and 'status' in e for e in errors))

    def test_invalid_status(self):
        data = valid_data('apod.json')
        data['status'] = 'weird'
        self.write_json(os.path.join('data', 'apod.json'), data)
        errors = validate_site(self.root)
        self.assertTrue(any('apod.json' in e and 'status' in e for e in errors))

    def test_unsafe_url_in_data(self):
        data = valid_data('apod.json')
        data['url'] = 'javascript:alert(1)'
        self.write_json(os.path.join('data', 'apod.json'), data)
        errors = validate_site(self.root)
        self.assertTrue(any('apod.json' in e and 'unsafe' in e for e in errors))

    def test_secret_leak_in_data(self):
        data = valid_data('near-earth.json')
        data['note'] = 'stored api_key=ABCDEFGH12345678'
        self.write_json(os.path.join('data', 'near-earth.json'), data)
        errors = validate_site(self.root)
        self.assertTrue(any('near-earth.json' in e and 'secret' in e for e in errors))

    def test_secret_leak_in_main_js(self):
        self.write('main.js', "const x = 'ASTRONOMY_APP_SECRET=SOMESECRETVALUE';\n")
        errors = validate_site(self.root)
        self.assertTrue(any('main.js' in e and 'secret' in e for e in errors))

    def test_wrong_canonical_url(self):
        self.build_valid_site()
        html = VALID_HTML.replace(CANONICAL_URL, 'https://example.com/other/')
        self.write('index.html', html)
        errors = validate_site(self.root)
        self.assertTrue(any('canonical' in e for e in errors))

    def test_missing_description(self):
        self.build_valid_site()
        html = VALID_HTML.replace(
            '<meta name="description" content="Observación astronómica desde Sevilla.">\n', '')
        self.write('index.html', html)
        errors = validate_site(self.root)
        self.assertTrue(any('description' in e for e in errors))

    def test_local_path_leak(self):
        self.build_valid_site()
        self.write('main.js', "const p = 'C:\\Users\\valen\\astroaida';\n")
        errors = validate_site(self.root)
        self.assertTrue(any('main.js' in e and 'path' in e for e in errors))

    def test_empty_link(self):
        self.build_valid_site()
        html = VALID_HTML.replace('</body>', '<a href="#">Enlace vacio</a></body>')
        self.write('index.html', html)
        errors = validate_site(self.root)
        self.assertTrue(any('empty' in e for e in errors))

    def test_unsafe_blank_link(self):
        self.build_valid_site()
        html = VALID_HTML.replace(
            '</body>', '<a href="https://nasa.gov" target="_blank">NASA</a></body>')
        self.write('index.html', html)
        errors = validate_site(self.root)
        self.assertTrue(any('noopener' in e for e in errors))

    def test_missing_asset(self):
        self.build_valid_site()
        self.write('index.html', VALID_HTML.replace('href="styles.css"', 'href="missing.css"'))
        errors = validate_site(self.root)
        self.assertTrue(any('missing.css' in e for e in errors))

    def test_moon_json_requires_image_url_for_compatibility(self):
        self.build_valid_site()
        data = valid_data('moon.json')
        del data['image_url']
        self.write_json(os.path.join('data', 'moon.json'), data)
        errors = validate_site(self.root)
        self.assertTrue(any('moon.json' in e and 'image_url' in e for e in errors))

    def test_missing_moon_renderer_script(self):
        self.build_valid_site()
        html = VALID_HTML.replace('<script src="moon-renderer.js"></script>\n', '')
        self.write('index.html', html)
        errors = validate_site(self.root)
        self.assertTrue(any('moon-renderer.js' in e for e in errors))

    def test_moon_renderer_must_load_before_main(self):
        self.build_valid_site()
        html = VALID_HTML.replace(
            '<script src="moon-renderer.js"></script>\n<script src="main.js"></script>',
            '<script src="main.js"></script>\n<script src="moon-renderer.js"></script>')
        self.write('index.html', html)
        errors = validate_site(self.root)
        self.assertTrue(any('before main.js' in e for e in errors))

    def test_valid_site_passes(self):
        self.build_valid_site()
        errors = validate_site(self.root)
        self.assertEqual(errors, [])


class TestValidateDataFile(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_missing_file(self):
        errors = validate_data_file(self.root, 'data/apod.json')
        self.assertTrue(any('missing' in e for e in errors))

    def test_valid_file(self):
        os.makedirs(os.path.join(self.root, 'data'), exist_ok=True)
        with open(os.path.join(self.root, 'data', 'apod.json'), 'w') as f:
            json.dump(valid_data('apod.json'), f)
        self.assertEqual(validate_data_file(self.root, 'data/apod.json'), [])


class TestValidateHtml(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_missing_html(self):
        errors = validate_html(self.root)
        self.assertTrue(any('index.html' in e for e in errors))

    def test_file_url_leak(self):
        with open(os.path.join(self.root, 'index.html'), 'w') as f:
            f.write(VALID_HTML.replace('</body>', '<img src="file:///etc/passwd"></body>'))
        errors = validate_html(self.root)
        self.assertTrue(any('unsafe' in e for e in errors))

    def test_root_relative_asset(self):
        with open(os.path.join(self.root, 'index.html'), 'w') as f:
            f.write(VALID_HTML.replace('href="styles.css"', 'href="/astroaida/styles.css"'))
        errors = validate_html(self.root)
        self.assertTrue(any('root-relative' in e for e in errors))


if __name__ == '__main__':
    unittest.main()