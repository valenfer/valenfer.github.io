import unittest
import http.client
import json
import io
import os
import sys
import tempfile
import urllib.parse
from contextlib import ExitStack, redirect_stdout
from datetime import datetime
from unittest.mock import patch, Mock
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import collect_data
from collect_data import (
    normalize_apod, normalize_neo, normalize_astronomy_positions, normalize_astronomy_moon,
    normalize_star_chart, validate_dataset, fetch_with_retry, write_json_atomically,
    build_apod_url, build_neo_url, fetch_apod, fetch_neo, fetch_astronomy_positions,
    fetch_astronomy_moon, fetch_astronomy_star_chart, collect_real, write_preview_datasets,
    fetch_weather_open_meteo, main
)

FIXED_NOW = datetime.fromisoformat('2026-08-11T21:30:45+02:00')


class TestAPODNormalization(unittest.TestCase):
    def setUp(self):
        self.fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

    def load_fixture(self, name):
        with open(os.path.join(self.fixture_dir, name), 'r') as f:
            return json.load(f)

    def test_normalize_apod_image(self):
        raw = self.load_fixture('nasa-apod-image.json')
        normalized = normalize_apod(raw)

        self.assertEqual(normalized['media_type'], 'image')
        self.assertEqual(normalized['url'], raw['url'])
        self.assertEqual(normalized['title'], raw['title'])
        self.assertEqual(normalized['explanation'], raw['explanation'])
        self.assertEqual(normalized['date'], raw['date'])
        self.assertIn('copyright', normalized)
        self.assertEqual(normalized['source'], 'NASA APOD')
        self.assertIn('fetched_at', normalized)

    def test_normalize_apod_video(self):
        raw = self.load_fixture('nasa-apod-video.json')
        normalized = normalize_apod(raw)

        self.assertEqual(normalized['media_type'], 'video')
        self.assertEqual(normalized['url'], raw['url'])
        self.assertEqual(normalized['title'], raw['title'])
        self.assertEqual(normalized['explanation'], raw['explanation'])
        self.assertEqual(normalized['date'], raw['date'])
        self.assertNotIn('copyright', normalized)
        self.assertEqual(normalized['source'], 'NASA APOD')
        self.assertIn('fetched_at', normalized)

    def test_normalize_apod_missing_copyright(self):
        raw = self.load_fixture('nasa-apod-image.json')
        del raw['copyright']
        normalized = normalize_apod(raw)
        self.assertNotIn('copyright', normalized)

    def test_normalize_apod_requires_media_type(self):
        raw = self.load_fixture('nasa-apod-image.json')
        del raw['media_type']
        with self.assertRaises(ValueError):
            normalize_apod(raw)

    def test_normalize_apod_requires_url(self):
        raw = self.load_fixture('nasa-apod-image.json')
        del raw['url']
        with self.assertRaises(ValueError):
            normalize_apod(raw)


class TestNeoNormalization(unittest.TestCase):
    def setUp(self):
        self.fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

    def load_fixture(self, name):
        with open(os.path.join(self.fixture_dir, name), 'r') as f:
            return json.load(f)

    def test_normalize_neo_feed(self):
        raw = self.load_fixture('nasa-neo.json')
        normalized = normalize_neo(raw)

        self.assertEqual(normalized['source'], 'NASA NeoWs')
        self.assertIn('fetched_at', normalized)
        self.assertIn('asteroids', normalized)
        self.assertEqual(len(normalized['asteroids']), 2)

        asteroid = normalized['asteroids'][0]
        self.assertEqual(asteroid['date'], '2024-01-15')
        self.assertEqual(asteroid['name'], '(2024 AB1)')
        self.assertIn('estimated_diameter_km', asteroid)
        self.assertEqual(asteroid['estimated_diameter_km']['min'], 0.1)
        self.assertEqual(asteroid['estimated_diameter_km']['max'], 0.2)
        self.assertIn('miss_distance_km', asteroid)
        self.assertEqual(asteroid['miss_distance_km'], 7500000)
        self.assertIn('velocity_km_s', asteroid)
        self.assertEqual(asteroid['velocity_km_s'], 15.5)
        self.assertEqual(asteroid['hazardous'], False)
        self.assertEqual(asteroid['nasa_url'], 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#obj=3542519')

        asteroid2 = normalized['asteroids'][1]
        self.assertEqual(asteroid2['date'], '2024-01-16')
        self.assertEqual(asteroid2['name'], '(2024 AB2)')
        self.assertEqual(asteroid2['estimated_diameter_km']['min'], 0.3)
        self.assertEqual(asteroid2['estimated_diameter_km']['max'], 0.6)
        self.assertEqual(asteroid2['miss_distance_km'], 3000000)
        self.assertEqual(asteroid2['velocity_km_s'], 22.3)
        self.assertEqual(asteroid2['hazardous'], True)
        self.assertEqual(asteroid2['nasa_url'], 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#obj=3542520')


class TestAstronomyPositionsNormalization(unittest.TestCase):
    def setUp(self):
        self.fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

    def load_fixture(self, name):
        with open(os.path.join(self.fixture_dir, name), 'r') as f:
            return json.load(f)

    def test_normalize_astronomy_positions_nested_structure(self):
        raw = self.load_fixture('astronomy-positions.json')
        normalized = normalize_astronomy_positions(raw)

        self.assertEqual(normalized['source'], 'AstronomyAPI')
        self.assertIn('fetched_at', normalized)
        self.assertIn('bodies', normalized)
        self.assertEqual(len(normalized['bodies']), 6)

        mercury = normalized['bodies'][0]
        self.assertEqual(mercury['name'], 'Mercury')
        self.assertEqual(mercury['altitude'], 15.2)
        self.assertEqual(mercury['azimuth'], 245.3)
        self.assertEqual(mercury['constellation'], 'Sagittarius')
        self.assertAlmostEqual(mercury['distance_km'], 109675000.18504)
        self.assertEqual(mercury['magnitude'], -0.5)

        moon = normalized['bodies'][5]
        self.assertEqual(moon['name'], 'Moon')
        self.assertEqual(moon['constellation'], 'Ophiuchus')
        self.assertAlmostEqual(moon['distance_km'], 378500.0)
        self.assertEqual(moon['phase'], 'Waxing Gibbous')
        self.assertEqual(moon['illumination'], 0.78)

        self.assertEqual(normalized['observer']['latitude'], 37.38283)
        self.assertEqual(normalized['observer']['longitude'], -5.97317)
        self.assertEqual(normalized['observer']['elevation'], 0)
        self.assertEqual(normalized['observer']['label'], 'Sevilla')

    def test_normalize_astronomy_positions_missing_extra_info(self):
        raw = self.load_fixture('astronomy-positions.json')
        del raw['data']['rows'][0]['positions'][0]['extraInfo']
        normalized = normalize_astronomy_positions(raw)
        self.assertNotIn('magnitude', normalized['bodies'][0])

    def test_normalize_astronomy_positions_null_optional_fields(self):
        raw = self.load_fixture('astronomy-positions-null.json')
        normalized = normalize_astronomy_positions(raw)

        sun = normalized['bodies'][0]
        self.assertEqual(sun['name'], 'Sun')
        self.assertNotIn('magnitude', sun)
        self.assertNotIn('phase', sun)
        self.assertNotIn('illumination', sun)
        self.assertEqual(sun['altitude'], 10.5)
        self.assertEqual(sun['azimuth'], 265.1)
        self.assertAlmostEqual(sun['distance_km'], 151000000.0)
        self.assertEqual(sun['constellation'], 'Leo')

        mercury = normalized['bodies'][1]
        self.assertEqual(mercury['name'], 'Mercury')
        self.assertEqual(mercury['magnitude'], -0.5)

    def test_normalize_astronomy_positions_excludes_earth(self):
        raw = self.load_fixture('astronomy-positions.json')
        earth = json.loads(json.dumps(raw['data']['rows'][0]))
        earth['body'] = {'id': 'earth', 'name': 'Earth'}
        earth['positions'][0]['id'] = 'earth'
        earth['positions'][0]['name'] = 'Earth'
        raw['data']['rows'].insert(0, earth)

        normalized = normalize_astronomy_positions(raw)

        self.assertNotIn('Earth', [body['name'] for body in normalized['bodies']])
        self.assertEqual(len(normalized['bodies']), 6)

    def test_normalize_astronomy_positions_missing_required_field_fails(self):
        for field in ('altitude', 'azimuth', 'distance'):
            with self.subTest(field=field):
                raw = self.load_fixture('astronomy-positions.json')
                position = raw['data']['rows'][0]['positions'][0]
                if field == 'altitude':
                    del position['position']['horizontal']['altitude']
                elif field == 'azimuth':
                    del position['position']['horizontal']['azimuth']
                else:
                    del position['distance']['fromEarth']['km']
                with self.assertRaises(ValueError):
                    normalize_astronomy_positions(raw)

    def test_normalize_astronomy_positions_requires_rows_structure(self):
        with self.assertRaises(ValueError):
            normalize_astronomy_positions({'data': {}})


class TestAstronomyMoonNormalization(unittest.TestCase):
    def setUp(self):
        self.fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

    def load_fixture(self, name):
        with open(os.path.join(self.fixture_dir, name), 'r') as f:
            return json.load(f)

    def test_normalize_astronomy_moon_combines_positions_and_phase_image(self):
        positions_raw = self.load_fixture('astronomy-positions.json')
        phase_raw = self.load_fixture('astronomy-moon.json')
        normalized = normalize_astronomy_moon(positions_raw, phase_raw)

        self.assertEqual(normalized['source'], 'AstronomyAPI')
        self.assertIn('fetched_at', normalized)
        self.assertEqual(normalized['phase'], 'Waxing Gibbous')
        self.assertEqual(normalized['illumination'], 0.78)
        self.assertAlmostEqual(normalized['distance_km'], 378500.0)
        self.assertEqual(
            normalized['image_url'],
            'https://widgets.astronomyapi.com/moon-phase/generated/20260811.png'
        )

        self.assertEqual(normalized['observer']['latitude'], 37.38283)
        self.assertEqual(normalized['observer']['longitude'], -5.97317)
        self.assertEqual(normalized['observer']['elevation'], 0)
        self.assertEqual(normalized['observer']['label'], 'Sevilla')

        self.assertNotIn('age_days', normalized)
        self.assertNotIn('next_new_moon', normalized)
        self.assertNotIn('next_full_moon', normalized)
        self.assertNotIn('angular_diameter_arcmin', normalized)
        self.assertNotIn('image', normalized)

    def test_normalize_astronomy_moon_requires_image_url(self):
        positions_raw = self.load_fixture('astronomy-positions.json')
        phase_raw = self.load_fixture('astronomy-moon.json')
        del phase_raw['data']['imageUrl']
        with self.assertRaises(ValueError):
            normalize_astronomy_moon(positions_raw, phase_raw)

    def test_normalize_astronomy_moon_requires_moon_row(self):
        phase_raw = self.load_fixture('astronomy-moon.json')
        positions_raw = self.load_fixture('astronomy-positions.json')
        positions_raw['data']['rows'] = [
            row for row in positions_raw['data']['rows']
            if row.get('body', {}).get('id') != 'moon'
        ]
        with self.assertRaises(ValueError):
            normalize_astronomy_moon(positions_raw, phase_raw)


class TestFetchWithRetry(unittest.TestCase):
    def _make_mock_response(self, data, status=200):
        mock_response = Mock()
        mock_response.read.return_value = data.encode('utf-8') if isinstance(data, str) else data
        mock_response.getcode.return_value = status
        mock_response.headers = {}
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        return mock_response

    def test_fetch_success(self):
        mock_response = self._make_mock_response('{"key": "value"}')

        with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
            result = fetch_with_retry('https://api.example.com/data', timeout=5, max_retries=3)
            self.assertEqual(result, {'key': 'value'})
            mock_urlopen.assert_called_once()

    def test_fetch_http_429_retry(self):
        error_429 = HTTPError('https://api.example.com/data', 429, 'Too Many Requests', {}, None)
        mock_response = self._make_mock_response('{"key": "value"}')

        with patch('urllib.request.urlopen', side_effect=[error_429, mock_response]) as mock_urlopen:
            result = fetch_with_retry('https://api.example.com/data', timeout=5, max_retries=3)
            self.assertEqual(result, {'key': 'value'})
            self.assertEqual(mock_urlopen.call_count, 2)

    def test_fetch_http_504_retry(self):
        error_504 = HTTPError('https://api.example.com/data', 504, 'Gateway Timeout', {}, None)
        mock_response = self._make_mock_response('{"key": "value"}')

        with patch('urllib.request.urlopen', side_effect=[error_504, mock_response]) as mock_urlopen:
            result = fetch_with_retry('https://api.example.com/data', timeout=5, max_retries=3)
            self.assertEqual(result, {'key': 'value'})
            self.assertEqual(mock_urlopen.call_count, 2)

    def test_fetch_http_400_no_retry(self):
        error_400 = HTTPError('https://api.example.com/data', 400, 'Bad Request', {}, None)

        with patch('urllib.request.urlopen', side_effect=error_400) as mock_urlopen:
            result = fetch_with_retry('https://api.example.com/data', timeout=5, max_retries=3)
            self.assertIsNone(result)
            mock_urlopen.assert_called_once()

    def test_fetch_timeout_retry(self):
        timeout_error = URLError('timeout')
        mock_response = self._make_mock_response('{"key": "value"}')

        with patch('urllib.request.urlopen', side_effect=[timeout_error, mock_response]) as mock_urlopen:
            result = fetch_with_retry('https://api.example.com/data', timeout=5, max_retries=3)
            self.assertEqual(result, {'key': 'value'})
            self.assertEqual(mock_urlopen.call_count, 2)

    def test_fetch_incomplete_read_retries_and_succeeds(self):
        response = self._make_mock_response('{"ok": true}')
        with patch('urllib.request.urlopen', side_effect=[
                http.client.IncompleteRead(b'partial'), response]) as mock_urlopen, \
                patch('time.sleep'):
            result = fetch_with_retry('https://api.example.com/data', max_retries=1,
                                      label='NASA APOD')

        self.assertEqual(result, {'ok': True})
        self.assertEqual(mock_urlopen.call_count, 2)

    def test_fetch_incomplete_read_exhausted_logs_network_error(self):
        output = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=[
                http.client.IncompleteRead(b'partial'),
                http.client.IncompleteRead(b'partial')]), \
                patch('time.sleep'), redirect_stdout(output):
            result = fetch_with_retry('https://api.example.com/data', max_retries=1,
                                      label='NASA APOD')

        self.assertIsNone(result)
        self.assertIn('NASA APOD: network error', output.getvalue())

    def test_fetch_malformed_json(self):
        mock_response = self._make_mock_response('not valid json')

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = fetch_with_retry('https://api.example.com/data', timeout=5, max_retries=3)
            self.assertIsNone(result)

    def test_fetch_http_400_logs_sanitized_message(self):
        fake_key = 'FAKEKEY12345'
        error_400 = HTTPError('https://api.example.com/data?api_key=' + fake_key, 400, 'Bad Request', {}, None)
        buf = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=error_400), redirect_stdout(buf):
            result = fetch_with_retry(
                'https://api.example.com/data?api_key=' + fake_key, timeout=5, max_retries=2,
                label='NASA APOD')
        self.assertIsNone(result)
        out = buf.getvalue()
        self.assertIn('NASA APOD: HTTP 400', out)
        self.assertNotIn(fake_key, out)

    def test_fetch_http_429_exhausted_logs_sanitized_message(self):
        fake_key = 'FAKEKEY12345'
        error_429 = HTTPError('https://api.example.com/data?api_key=' + fake_key, 429, 'Too Many Requests', {}, None)
        buf = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=error_429), redirect_stdout(buf):
            result = fetch_with_retry(
                'https://api.example.com/data?api_key=' + fake_key, timeout=5, max_retries=1,
                label='NASA NeoWs')
        self.assertIsNone(result)
        out = buf.getvalue()
        self.assertIn('NASA NeoWs: HTTP 429', out)
        self.assertNotIn(fake_key, out)

    def test_fetch_urlerror_logs_network_error_sanitized(self):
        fake_key = 'FAKEKEY12345'
        err = URLError('timeout')
        buf = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=err), redirect_stdout(buf):
            result = fetch_with_retry(
                'https://api.example.com/data?api_key=' + fake_key, timeout=5, max_retries=1,
                label='AstronomyAPI positions')
        self.assertIsNone(result)
        out = buf.getvalue()
        self.assertIn('AstronomyAPI positions: network error', out)
        self.assertNotIn(fake_key, out)

    def test_fetch_malformed_json_logs_sanitized_message(self):
        fake_key = 'FAKEKEY12345'
        mock_response = self._make_mock_response('not valid json')
        buf = io.StringIO()
        with patch('urllib.request.urlopen', return_value=mock_response), redirect_stdout(buf):
            result = fetch_with_retry(
                'https://api.example.com/data?api_key=' + fake_key, timeout=5, max_retries=2,
                label='AstronomyAPI moon')
        self.assertIsNone(result)
        out = buf.getvalue()
        self.assertIn('AstronomyAPI moon: invalid JSON', out)
        self.assertNotIn(fake_key, out)

    def test_fetch_unexpected_error_logs_sanitized_message(self):
        fake_key = 'FAKEKEY12345'
        buf = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=RuntimeError('boom')), redirect_stdout(buf):
            result = fetch_with_retry(
                'https://api.example.com/data?api_key=' + fake_key, timeout=5, max_retries=2,
                label='AstronomyAPI star-chart')
        self.assertIsNone(result)
        out = buf.getvalue()
        self.assertIn('AstronomyAPI star-chart: unexpected client error', out)
        self.assertNotIn(fake_key, out)

    def test_fetch_header_fake_key_not_logged(self):
        fake_key = 'FAKEKEY12345'
        error_400 = HTTPError('https://api.example.com/data', 400, 'Bad Request', {}, None)
        buf = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=error_400), redirect_stdout(buf):
            result = fetch_with_retry(
                'https://api.example.com/data', timeout=5, max_retries=2, label='NASA APOD',
                headers={'Authorization': 'Basic ' + fake_key})
        self.assertIsNone(result)
        self.assertIn('NASA APOD: HTTP 400', buf.getvalue())
        self.assertNotIn(fake_key, buf.getvalue())

    def test_fetch_no_output_on_successful_retry(self):
        error_429 = HTTPError('https://api.example.com/data', 429, 'Too Many Requests', {}, None)
        mock_response = self._make_mock_response('{"key": "value"}')
        buf = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=[error_429, mock_response]), redirect_stdout(buf):
            result = fetch_with_retry('https://api.example.com/data', timeout=5, max_retries=3, label='NASA APOD')
        self.assertEqual(result, {'key': 'value'})
        self.assertEqual(buf.getvalue(), '')

    def test_fetch_sanitizes_unsafe_label(self):
        error_400 = HTTPError('https://api.example.com/data', 400, 'Bad Request', {}, None)
        buf = io.StringIO()
        with patch('urllib.request.urlopen', side_effect=error_400), redirect_stdout(buf):
            fetch_with_retry('https://api.example.com/data', timeout=5, max_retries=2,
                             label='source "quoted"\n<tag>')
        out = buf.getvalue()
        self.assertNotIn('"', out)
        self.assertNotIn('<', out)
        self.assertNotIn('\n', out.strip())
        self.assertIn('source quotedtag: HTTP 400', out)

    def test_fetch_no_credentials_in_success_log(self):
        fake_key = 'FAKEKEY12345'
        mock_response = self._make_mock_response('{"key": "value"}')
        buf = io.StringIO()
        with patch('urllib.request.urlopen', return_value=mock_response), redirect_stdout(buf):
            result = fetch_with_retry(
                'https://api.example.com/data?api_key=' + fake_key, timeout=5, max_retries=2,
                label='NASA APOD', headers={'Authorization': 'Basic ' + fake_key})
        self.assertEqual(result, {'key': 'value'})
        self.assertNotIn(fake_key, buf.getvalue())

    def test_fetch_max_retries_exceeded(self):
        error_504 = HTTPError('https://api.example.com/data', 504, 'Gateway Timeout', {}, None)

        with patch('urllib.request.urlopen', side_effect=error_504) as mock_urlopen:
            result = fetch_with_retry('https://api.example.com/data', timeout=5, max_retries=2)
            self.assertIsNone(result)
            self.assertEqual(mock_urlopen.call_count, 3)

    def test_fetch_no_auth_logging(self):
        mock_response = self._make_mock_response('{"key": "value"}')

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.return_value = mock_response
            fetch_with_retry('https://api.example.com/data?api_key=SECRET_KEY', timeout=5)
            called_args = mock_urlopen.call_args
            if called_args:
                called_url = called_args[0][0]
                if hasattr(called_url, 'full_url'):
                    called_url = called_url.full_url
                self.assertIn('SECRET_KEY', str(called_url))


class TestFetchWeatherOpenMeteo(unittest.TestCase):
    def _make_weather_response(self, hours_data):
        """Create a mock Open-Meteo response with hourly data."""
        hourly = {
            'time': [h['time'] for h in hours_data],
            'cloud_cover': [h.get('cloud_cover') for h in hours_data],
            'visibility': [h.get('visibility') for h in hours_data],
            'precipitation_probability': [h.get('precipitation_probability') for h in hours_data],
            'temperature_2m': [h.get('temperature_2m') for h in hours_data],
        }
        return {'hourly': hourly}

    @patch('collect_data.fetch_with_retry')
    @patch('collect_data.horizontal_coordinates')
    def test_fetch_weather_filters_to_observation_window(self, mock_horiz, mock_fetch):
        """Weather should only include hours within observation_window (target_date 00:00 to next_day 12:00)."""
        target_date = '2026-08-12'
        tz = ZoneInfo('Europe/Madrid')

        hours_data = [
            # Night before target_date (should be excluded)
            {'time': '2026-08-11T22:00:00+02:00', 'cloud_cover': 10, 'visibility': 10000, 'precipitation_probability': 0, 'temperature_2m': 22.0},
            {'time': '2026-08-11T23:00:00+02:00', 'cloud_cover': 10, 'visibility': 10000, 'precipitation_probability': 0, 'temperature_2m': 21.0},
            # Target date day hours (not dark, excluded by darkness check)
            {'time': '2026-08-12T10:00:00+02:00', 'cloud_cover': 50, 'visibility': 8000, 'precipitation_probability': 10, 'temperature_2m': 30.0},
            # Target date night hours (should be included - within observation_window)
            {'time': '2026-08-12T22:00:00+02:00', 'cloud_cover': 20, 'visibility': 12000, 'precipitation_probability': 5, 'temperature_2m': 24.0},
            {'time': '2026-08-12T23:00:00+02:00', 'cloud_cover': 30, 'visibility': 11000, 'precipitation_probability': 10, 'temperature_2m': 23.0},
            {'time': '2026-08-13T00:00:00+02:00', 'cloud_cover': 40, 'visibility': 10000, 'precipitation_probability': 15, 'temperature_2m': 22.0},
            {'time': '2026-08-13T01:00:00+02:00', 'cloud_cover': 50, 'visibility': 9000, 'precipitation_probability': 20, 'temperature_2m': 21.0},
            {'time': '2026-08-13T02:00:00+02:00', 'cloud_cover': 60, 'visibility': 8000, 'precipitation_probability': 25, 'temperature_2m': 20.0},
            {'time': '2026-08-13T03:00:00+02:00', 'cloud_cover': 70, 'visibility': 7000, 'precipitation_probability': 30, 'temperature_2m': 19.0},
            {'time': '2026-08-13T04:00:00+02:00', 'cloud_cover': 80, 'visibility': 6000, 'precipitation_probability': 35, 'temperature_2m': 18.0},
            {'time': '2026-08-13T05:00:00+02:00', 'cloud_cover': 90, 'visibility': 5000, 'precipitation_probability': 40, 'temperature_2m': 17.0},
            # Next day morning hours (should be included - within observation_window until 12:00)
            {'time': '2026-08-13T06:00:00+02:00', 'cloud_cover': 95, 'visibility': 4000, 'precipitation_probability': 45, 'temperature_2m': 16.5},
            {'time': '2026-08-13T07:00:00+02:00', 'cloud_cover': 90, 'visibility': 4500, 'precipitation_probability': 40, 'temperature_2m': 16.0},
            {'time': '2026-08-13T08:00:00+02:00', 'cloud_cover': 80, 'visibility': 5000, 'precipitation_probability': 35, 'temperature_2m': 17.0},
            {'time': '2026-08-13T09:00:00+02:00', 'cloud_cover': 70, 'visibility': 6000, 'precipitation_probability': 30, 'temperature_2m': 19.0},
            {'time': '2026-08-13T10:00:00+02:00', 'cloud_cover': 60, 'visibility': 7000, 'precipitation_probability': 25, 'temperature_2m': 21.0},
            {'time': '2026-08-13T11:00:00+02:00', 'cloud_cover': 50, 'visibility': 8000, 'precipitation_probability': 20, 'temperature_2m': 23.0},
            {'time': '2026-08-13T12:00:00+02:00', 'cloud_cover': 40, 'visibility': 9000, 'precipitation_probability': 15, 'temperature_2m': 25.0},
            # Next day afternoon (should be excluded - after observation_window ends at 12:00)
            {'time': '2026-08-13T13:00:00+02:00', 'cloud_cover': 30, 'visibility': 10000, 'precipitation_probability': 10, 'temperature_2m': 27.0},
            # Next night (should be excluded - after observation_window)
            {'time': '2026-08-13T22:00:00+02:00', 'cloud_cover': 10, 'visibility': 10000, 'precipitation_probability': 0, 'temperature_2m': 22.0},
        ]

        # Mock all hours as dark (sun altitude <= -6) except day hours
        def mock_horiz_func(body, dt):
            hour = dt.hour
            if 7 <= hour < 21:
                return {'sun_altitude_deg': 30.0, 'altitude_deg': 0, 'azimuth_deg': 0}
            return {'sun_altitude_deg': -20.0, 'altitude_deg': 0, 'azimuth_deg': 0}

        mock_horiz.side_effect = mock_horiz_func
        mock_fetch.return_value = self._make_weather_response(hours_data)

        result = fetch_weather_open_meteo(target_date)

        self.assertIsNotNone(result)
        # Should only include hours from 2026-08-12T22:00 to 2026-08-13T12:00 (dark hours only)
        # Dark hours in that window: 22:00, 23:00, 00:00, 01:00, 02:00, 03:00, 04:00, 05:00, 06:00
        # That's 9 hours
        # Note: 07:00+ are not dark (sun altitude > -6 in our mock)

        # Cloud cover average of included hours
        included_hours = [
            20, 30, 40, 50, 60, 70, 80, 90, 95  # 22:00 to 06:00
        ]
        expected_cloud = sum(included_hours) / len(included_hours)
        self.assertAlmostEqual(result['cloud_cover'], expected_cloud, places=1)

        # Max visibility of included hours
        included_vis = [12000, 11000, 10000, 9000, 8000, 7000, 6000, 5000, 4000]
        self.assertEqual(result['visibility'], max(included_vis))

        # Max precipitation of included hours
        included_precip = [5, 10, 15, 20, 25, 30, 35, 40, 45]
        self.assertEqual(result['precipitation_probability'], max(included_precip))

        # Average temperature of included hours
        included_temp = [24.0, 23.0, 22.0, 21.0, 20.0, 19.0, 18.0, 17.0, 16.5]
        expected_temp = round(sum(included_temp) / len(included_temp), 1)
        self.assertEqual(result['temperature'], expected_temp)

    @patch('collect_data.fetch_with_retry')
    @patch('collect_data.horizontal_coordinates')
    def test_fetch_weather_excludes_hours_before_target_date(self, mock_horiz, mock_fetch):
        """Hours before target_date 00:00 should be excluded even if dark."""
        target_date = '2026-08-12'

        hours_data = [
            # Night before target_date (dark but before observation_window)
            {'time': '2026-08-11T22:00:00+02:00', 'cloud_cover': 10, 'visibility': 10000, 'precipitation_probability': 0, 'temperature_2m': 22.0},
            {'time': '2026-08-11T23:00:00+02:00', 'cloud_cover': 10, 'visibility': 10000, 'precipitation_probability': 0, 'temperature_2m': 21.0},
            # Target date night (should be included)
            {'time': '2026-08-12T22:00:00+02:00', 'cloud_cover': 50, 'visibility': 5000, 'precipitation_probability': 50, 'temperature_2m': 20.0},
        ]

        def mock_horiz_func(body, dt):
            return {'sun_altitude_deg': -20.0, 'altitude_deg': 0, 'azimuth_deg': 0}

        mock_horiz.side_effect = mock_horiz_func
        mock_fetch.return_value = self._make_weather_response(hours_data)

        result = fetch_weather_open_meteo(target_date)

        self.assertIsNotNone(result)
        # Should only include 2026-08-12T22:00 (cloud=50, vis=5000, precip=50, temp=20)
        self.assertEqual(result['cloud_cover'], 50.0)
        self.assertEqual(result['visibility'], 5000)
        self.assertEqual(result['precipitation_probability'], 50)
        self.assertEqual(result['temperature'], 20.0)

    @patch('collect_data.fetch_with_retry')
    @patch('collect_data.horizontal_coordinates')
    def test_fetch_weather_excludes_hours_after_observation_window(self, mock_horiz, mock_fetch):
        """Hours after next_day 12:00 should be excluded even if dark."""
        target_date = '2026-08-12'

        hours_data = [
            # Target date night (should be included)
            {'time': '2026-08-12T22:00:00+02:00', 'cloud_cover': 50, 'visibility': 5000, 'precipitation_probability': 50, 'temperature_2m': 20.0},
            # Next night (dark but after observation_window)
            {'time': '2026-08-13T22:00:00+02:00', 'cloud_cover': 10, 'visibility': 10000, 'precipitation_probability': 0, 'temperature_2m': 22.0},
            {'time': '2026-08-13T23:00:00+02:00', 'cloud_cover': 10, 'visibility': 10000, 'precipitation_probability': 0, 'temperature_2m': 21.0},
        ]

        def mock_horiz_func(body, dt):
            return {'sun_altitude_deg': -20.0, 'altitude_deg': 0, 'azimuth_deg': 0}

        mock_horiz.side_effect = mock_horiz_func
        mock_fetch.return_value = self._make_weather_response(hours_data)

        result = fetch_weather_open_meteo(target_date)

        self.assertIsNotNone(result)
        # Should only include 2026-08-12T22:00
        self.assertEqual(result['cloud_cover'], 50.0)
        self.assertEqual(result['visibility'], 5000)
        self.assertEqual(result['precipitation_probability'], 50)
        self.assertEqual(result['temperature'], 20.0)


class TestIcsEventInWindow(unittest.TestCase):
    def test_ics_event_in_window_returns_false_on_invalid_date(self):
        """_ics_event_in_window should return False for events with invalid/unparseable dates."""
        tz = ZoneInfo('Europe/Madrid')
        window_start = datetime(2026, 8, 12, 0, 0, tzinfo=tz)
        window_end = datetime(2026, 8, 13, 12, 0, tzinfo=tz)

        # Invalid dtstart
        ics_event_invalid = {'dtstart': 'not-a-date', 'summary': 'Test'}
        self.assertFalse(collect_data._ics_event_in_window(ics_event_invalid, window_start, window_end, tz))

        # Empty dtstart
        ics_event_empty = {'dtstart': '', 'summary': 'Test'}
        self.assertFalse(collect_data._ics_event_in_window(ics_event_empty, window_start, window_end, tz))

        # Malformed dtstart
        ics_event_malformed = {'dtstart': '2026-13-45T99:99:99', 'summary': 'Test'}
        self.assertFalse(collect_data._ics_event_in_window(ics_event_malformed, window_start, window_end, tz))

    def test_ics_event_in_window_returns_true_for_valid_in_window(self):
        """_ics_event_in_window should return True for valid dates within window."""
        tz = ZoneInfo('Europe/Madrid')
        window_start = datetime(2026, 8, 12, 0, 0, tzinfo=tz)
        window_end = datetime(2026, 8, 13, 12, 0, tzinfo=tz)

        ics_event = {'dtstart': '20260812T200000Z', 'summary': 'Test'}
        self.assertTrue(collect_data._ics_event_in_window(ics_event, window_start, window_end, tz))

    def test_ics_event_in_window_returns_false_for_valid_out_of_window(self):
        """_ics_event_in_window should return False for valid dates outside window."""
        tz = ZoneInfo('Europe/Madrid')
        window_start = datetime(2026, 8, 12, 0, 0, tzinfo=tz)
        window_end = datetime(2026, 8, 13, 12, 0, tzinfo=tz)

        ics_event = {'dtstart': '20260815T200000Z', 'summary': 'Test'}
        self.assertFalse(collect_data._ics_event_in_window(ics_event, window_start, window_end, tz))


class TestParseIcsValidation(unittest.TestCase):
    def test_parse_ics_rejects_non_vcalendar(self):
        """parse_ics_events should return empty list for non-VCALENDAR content (e.g., HTML error pages)."""
        html_error = '<html><body>Error 500</body></html>'
        events = collect_data.parse_ics_events(html_error, 2026)
        self.assertEqual(events, [])

    def test_parse_ics_rejects_empty_content(self):
        """parse_ics_events should return empty list for empty content."""
        events = collect_data.parse_ics_events('', 2026)
        self.assertEqual(events, [])

    def test_parse_ics_rejects_vcalendar_without_vevent(self):
        """parse_ics_events should return empty list for VCALENDAR without VEVENT."""
        ics_no_events = 'BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR'
        events = collect_data.parse_ics_events(ics_no_events, 2026)
        self.assertEqual(events, [])

    def test_parse_ics_accepts_valid_vcalendar_with_vevent(self):
        """parse_ics_events should parse valid VCALENDAR with VEVENT."""
        ics_valid = '''BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20260812T200000Z
SUMMARY:Test Event
END:VEVENT
END:VCALENDAR'''
        events = collect_data.parse_ics_events(ics_valid, 2026)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['summary'], 'Test Event')


class TestEventDeduplication(unittest.TestCase):
    def test_normalize_ephemerides_deduplicates_events_by_id(self):
        """normalize_ephemerides should deduplicate events deterministically by ID."""
        from datetime import date
        tz = ZoneInfo('Europe/Madrid')
        target_date = date(2026, 8, 12)

        # Create duplicate events with same ID
        events = [
            {'id': 'eclipse-2026-08-12', 'type': 'solar_eclipse', 'title_es': 'Eclipse 1', 'summary_es': 'S1',
             'start_local': '2026-08-12T19:00+02:00', 'visibility': {'status': 'visible', 'label': 'V', 'reason': 'R'},
             'source': {'name': 'X', 'url': 'https://example.com'}},
            {'id': 'eclipse-2026-08-12', 'type': 'solar_eclipse', 'title_es': 'Eclipse 2', 'summary_es': 'S2',
             'start_local': '2026-08-12T20:00+02:00', 'visibility': {'status': 'visible', 'label': 'V', 'reason': 'R'},
             'source': {'name': 'X', 'url': 'https://example.com'}},
            {'id': 'other-event', 'type': 'conjunction', 'title_es': 'Conjunction', 'summary_es': 'S3',
             'start_local': '2026-08-12T21:00+02:00', 'visibility': {'status': 'visible', 'label': 'V', 'reason': 'R'},
             'source': {'name': 'X', 'url': 'https://example.com'}},
        ]

        normalized = collect_data.normalize_ephemerides(
            [], target_date, tz, None, events
        )
        ids = [event['id'] for event in normalized['events']]
        self.assertEqual(ids.count('eclipse-2026-08-12'), 1)
        self.assertEqual(ids.count('other-event'), 1)
        kept = next(event for event in normalized['events']
                    if event['id'] == 'eclipse-2026-08-12')
        self.assertEqual(kept['title_es'], 'Eclipse 1')

    def test_validate_ephemerides_rejects_duplicate_event_ids(self):
        """validate_ephemerides should reject events with duplicate IDs."""
        dataset = {
            'status': 'preview',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': '2026-08-12',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317, 'label': 'Sevilla'},
            'observation_window': {'start_local': '2026-08-12T00:00+02:00', 'end_local': '2026-08-13T12:00+02:00'},
            'events': [
                {'id': 'event-1', 'type': 'solar_eclipse', 'title_es': 'E1', 'summary_es': 'S1',
                 'start_local': '2026-08-12T19:00+02:00', 'visibility': {'status': 'visible', 'label': 'V', 'reason': 'R'},
                 'source': {'name': 'X', 'url': 'https://example.com'}},
                {'id': 'event-1', 'type': 'conjunction', 'title_es': 'E2', 'summary_es': 'S2',
                 'start_local': '2026-08-12T20:00+02:00', 'visibility': {'status': 'visible', 'label': 'V', 'reason': 'R'},
                 'source': {'name': 'X', 'url': 'https://example.com'}},
            ],
            'weather': {},
            'sources': [{'name': 'X', 'url': 'https://example.com'}],
        }
        errors = collect_data.validate_ephemerides(dataset)
        self.assertTrue(any('duplicate' in e.lower() or 'id' in e.lower() for e in errors),
                        f'Expected duplicate ID error, got: {errors}')

    def test_validate_ephemerides_accepts_unique_event_ids(self):
        """validate_ephemerides should accept events with unique IDs."""
        dataset = {
            'status': 'preview',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': '2026-08-12',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317, 'label': 'Sevilla'},
            'observation_window': {'start_local': '2026-08-12T00:00+02:00', 'end_local': '2026-08-13T12:00+02:00'},
            'events': [
                {'id': 'event-1', 'type': 'solar_eclipse', 'title_es': 'E1', 'summary_es': 'S1',
                 'start_local': '2026-08-12T19:00+02:00', 'visibility': {'status': 'visible', 'label': 'V', 'reason': 'R'},
                 'source': {'name': 'X', 'url': 'https://example.com'}},
                {'id': 'event-2', 'type': 'conjunction', 'title_es': 'E2', 'summary_es': 'S2',
                 'start_local': '2026-08-12T20:00+02:00', 'visibility': {'status': 'visible', 'label': 'V', 'reason': 'R'},
                 'source': {'name': 'X', 'url': 'https://example.com'}},
            ],
            'weather': {},
            'sources': [{'name': 'X', 'url': 'https://example.com'}],
        }
        errors = collect_data.validate_ephemerides(dataset)
        self.assertEqual(errors, [])


class TestTitleEsFromIcs(unittest.TestCase):
    def test_title_es_from_ics_known_events(self):
        """Known event types should return deterministic Spanish translations."""
        self.assertEqual(collect_data.title_es_from_ics('Solar Eclipse'), 'Eclipse solar')
        self.assertEqual(collect_data.title_es_from_ics('Lunar Eclipse'), 'Eclipse lunar')
        self.assertEqual(collect_data.title_es_from_ics('Meteor Shower'), 'Lluvia de meteoros')
        self.assertEqual(collect_data.title_es_from_ics('Conjunction'), 'Conjunción')
        self.assertEqual(collect_data.title_es_from_ics('Opposition'), 'Oposición')
        self.assertEqual(collect_data.title_es_from_ics('Full Moon'), 'Luna llena')
        self.assertEqual(collect_data.title_es_from_ics('New Moon'), 'Luna nueva')
        self.assertEqual(collect_data.title_es_from_ics('First Quarter'), 'Cuarto creciente')
        self.assertEqual(collect_data.title_es_from_ics('Last Quarter'), 'Cuarto menguante')

    def test_title_es_from_ics_unknown_event_returns_original(self):
        """Unknown events should return the original title (fallback)."""
        # These don't match any known pattern
        result = collect_data.title_es_from_ics('Unknown Event Type XYZ')
        self.assertEqual(result, 'Unknown Event Type XYZ')

        result = collect_data.title_es_from_ics('Random Astronomy Thing')
        self.assertEqual(result, 'Random Astronomy Thing')

        # Body names in unknown events are NOT partially translated
        result = collect_data.title_es_from_ics('Mercury at greatest elongation')
        self.assertEqual(result, 'Mercury at greatest elongation')

        result = collect_data.title_es_from_ics('Venus at dichotomy')
        self.assertEqual(result, 'Venus at dichotomy')

        result = collect_data.title_es_from_ics('Mars close approach')
        self.assertEqual(result, 'Mars close approach')

    def test_title_es_from_ics_no_hybrid_translations(self):
        """Result should not contain mixed English/Spanish - either known pattern or original."""
        # Known pattern fully translated
        result = collect_data.title_es_from_ics('Solar Eclipse on August 12')
        self.assertEqual(result, 'Eclipse solar')

        # Unknown event returned as-is (no partial translation)
        result = collect_data.title_es_from_ics('Comet C/2023 A3 passes into view')
        self.assertEqual(result, 'Comet C/2023 A3 passes into view')


class TestWriteJsonAtomically(unittest.TestCase):
    def test_write_json_atomically(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test.json')
            data = {'key': 'value', 'number': 42}
            write_json_atomically(filepath, data)

            self.assertTrue(os.path.exists(filepath))
            with open(filepath, 'r') as f:
                loaded = json.load(f)
            self.assertEqual(loaded, data)

    def test_write_json_atomically_preserves_on_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test.json')
            original_data = {'original': 'data'}
            write_json_atomically(filepath, original_data)

            class FailingWrite:
                def __init__(self, *args, **kwargs):
                    pass
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    return False
                def write(self, data):
                    raise IOError("Simulated write failure")

            with patch('builtins.open', side_effect=IOError("Simulated write failure")):
                try:
                    write_json_atomically(filepath, {'new': 'data'})
                except IOError:
                    pass

            with open(filepath, 'r') as f:
                loaded = json.load(f)
            self.assertEqual(loaded, original_data)


class TestStarChartNormalization(unittest.TestCase):
    def setUp(self):
        self.fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

    def load_fixture(self, name):
        with open(os.path.join(self.fixture_dir, name), 'r') as f:
            return json.load(f)

    def test_normalize_star_chart(self):
        raw = self.load_fixture('astronomy-star-chart.json')
        normalized = normalize_star_chart(raw)

        self.assertEqual(normalized['source'], 'AstronomyAPI')
        self.assertIn('fetched_at', normalized)
        self.assertEqual(
            normalized['image_url'],
            'https://widgets.astronomyapi.com/star-chart/generated/20260811.png'
        )
        self.assertNotIn('style', normalized)
        self.assertEqual(normalized['observer']['latitude'], 37.38283)
        self.assertEqual(normalized['observer']['longitude'], -5.97317)
        self.assertEqual(normalized['observer']['elevation'], 0)
        self.assertEqual(normalized['observer']['label'], 'Sevilla')

    def test_normalize_star_chart_missing_data(self):
        with self.assertRaises(ValueError):
            normalize_star_chart({})

    def test_normalize_star_chart_missing_image_url(self):
        raw = self.load_fixture('astronomy-star-chart.json')
        del raw['data']['imageUrl']
        with self.assertRaises(ValueError):
            normalize_star_chart(raw)

    def test_normalize_star_chart_observer_defaults(self):
        raw = self.load_fixture('astronomy-star-chart.json')
        normalized = normalize_star_chart(raw)
        self.assertEqual(normalized['observer']['latitude'], 37.38283)
        self.assertEqual(normalized['observer']['label'], 'Sevilla')


class TestDatasetValidation(unittest.TestCase):
    def _meta(self, status='live'):
        return {
            'source': 'NASA APOD',
            'fetched_at': '2026-08-11T12:00:00+00:00',
            'status': status,
        }

    def test_valid_apod_passes(self):
        dataset = dict(self._meta(), media_type='image', url='https://example.com/image.jpg')
        self.assertEqual(validate_dataset('apod.json', dataset), [])

    def test_apod_missing_meta_fields(self):
        dataset = {'media_type': 'image', 'url': 'https://example.com/image.jpg'}
        errors = validate_dataset('apod.json', dataset)
        self.assertIn('source', errors)
        self.assertIn('fetched_at', errors)
        self.assertIn('status', errors)

    def test_apod_bad_media_type(self):
        dataset = dict(self._meta(), media_type='audio', url='https://example.com/x')
        self.assertIn('media_type', validate_dataset('apod.json', dataset))

    def test_apod_missing_url(self):
        dataset = dict(self._meta(), media_type='image')
        self.assertIn('url', validate_dataset('apod.json', dataset))

    def test_valid_neo_passes(self):
        dataset = dict(
            self._meta(),
            asteroids=[{
                'date': '2026-08-11',
                'name': '(2026 XYZ1)',
                'estimated_diameter_km': {'min': 0.1, 'max': 0.2},
                'miss_distance_km': 4000000,
                'velocity_km_s': 18.2,
                'hazardous': False,
                'nasa_url': 'https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#obj=1',
            }],
        )
        self.assertEqual(validate_dataset('near-earth.json', dataset), [])

    def test_neo_missing_asteroid_field(self):
        dataset = dict(self._meta(), asteroids=[{'date': '2026-08-11', 'name': 'x'}])
        errors = validate_dataset('near-earth.json', dataset)
        self.assertTrue(any('miss_distance_km' in e for e in errors))

    def test_neo_missing_asteroids_list(self):
        dataset = dict(self._meta())
        self.assertIn('asteroids', validate_dataset('near-earth.json', dataset))

    def test_valid_positions_passes(self):
        dataset = dict(
            self._meta(),
            bodies=[{'name': 'Mercury', 'altitude': 15.2, 'azimuth': 245.3}],
            observer={'latitude': 37.38283, 'longitude': -5.97317, 'elevation': 0, 'label': 'Sevilla'},
        )
        self.assertEqual(validate_dataset('sky-today.json', dataset), [])

    def test_positions_missing_observer(self):
        dataset = dict(self._meta(), bodies=[{'name': 'Mercury'}])
        self.assertIn('observer', validate_dataset('sky-today.json', dataset))

    def test_valid_moon_passes(self):
        dataset = dict(
            self._meta(),
            phase='Gibosa creciente',
            image_url='https://widgets.astronomyapi.com/moon-phase/generated/x.png',
            observer={'latitude': 37.38283, 'longitude': -5.97317, 'elevation': 0, 'label': 'Sevilla'},
        )
        self.assertEqual(validate_dataset('moon.json', dataset), [])

    def test_moon_missing_phase(self):
        dataset = dict(self._meta(), observer={})
        self.assertIn('phase', validate_dataset('moon.json', dataset))

    def test_moon_missing_image_url(self):
        dataset = dict(self._meta(), phase='Gibosa creciente', observer={})
        self.assertIn('image_url', validate_dataset('moon.json', dataset))

    def test_valid_star_chart_passes(self):
        dataset = dict(
            self._meta(),
            image_url='https://widgets.astronomyapi.com/star-chart/generated/x.png',
        )
        self.assertEqual(validate_dataset('star-chart.json', dataset), [])

    def test_star_chart_missing_image_url(self):
        dataset = dict(self._meta())
        self.assertIn('image_url', validate_dataset('star-chart.json', dataset))

    def test_unknown_filename(self):
        with self.assertRaises(KeyError):
            validate_dataset('unknown.json', {})


class TestUrlBuilding(unittest.TestCase):
    def test_build_apod_url(self):
        url = build_apod_url('DEMO_KEY')
        self.assertIn('https://api.nasa.gov/planetary/apod', url)
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(parsed['api_key'], ['DEMO_KEY'])

    def test_build_neo_url_seven_day_window(self):
        url = build_neo_url('DEMO_KEY')
        self.assertIn('https://api.nasa.gov/neo/rest/v1/feed', url)
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        start = datetime.fromisoformat(parsed['start_date'][0]).date()
        end = datetime.fromisoformat(parsed['end_date'][0]).date()
        self.assertEqual((end - start).days, 6)


class TestFetchFunctions(unittest.TestCase):
    def test_fetch_apod(self):
        with patch('collect_data.fetch_with_retry') as mock_fetch:
            mock_fetch.return_value = {'ok': True}
            result = fetch_apod('KEY', timeout=5, max_retries=2)
        self.assertEqual(result, {'ok': True})
        url = mock_fetch.call_args[0][0]
        self.assertIn('https://api.nasa.gov/planetary/apod', url)
        self.assertIn('api_key=KEY', url)
        self.assertEqual(mock_fetch.call_args[1]['label'], 'NASA APOD')

    def test_fetch_neo(self):
        with patch('collect_data.fetch_with_retry') as mock_fetch:
            mock_fetch.return_value = {'ok': True}
            result = fetch_neo('KEY', timeout=5, max_retries=2)
        self.assertEqual(result, {'ok': True})
        url = mock_fetch.call_args[0][0]
        self.assertIn('https://api.nasa.gov/neo/rest/v1/feed', url)
        self.assertEqual(mock_fetch.call_args[1]['label'], 'NASA NeoWs')

    def test_fetch_astronomy_positions_sends_observer_and_auth(self):
        with patch('collect_data.astronomy_now', return_value=FIXED_NOW), \
                patch('collect_data.fetch_with_retry') as mock_fetch:
            mock_fetch.return_value = {'ok': True}
            result = fetch_astronomy_positions('ID', 'SECRET', timeout=5, max_retries=2)
        self.assertEqual(result, {'ok': True})
        url = mock_fetch.call_args[0][0]
        self.assertIn('https://api.astronomyapi.com/api/v2/bodies/positions', url)
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(parsed['latitude'], ['37.38283'])
        self.assertEqual(parsed['longitude'], ['-5.97317'])
        self.assertEqual(parsed['output'], ['rows'])
        self.assertEqual(parsed['from_date'], ['2026-08-11'])
        self.assertEqual(parsed['to_date'], ['2026-08-11'])
        self.assertEqual(parsed['time'], ['21:30:45'])
        headers = mock_fetch.call_args[1]['headers']
        self.assertIn('Authorization', headers)
        self.assertTrue(headers['Authorization'].startswith('Basic '))
        self.assertEqual(mock_fetch.call_args[1]['label'], 'AstronomyAPI positions')

    def test_fetch_astronomy_moon_posts_minimal_documented_payload_with_date(self):
        with patch('collect_data.astronomy_now', return_value=FIXED_NOW), \
                patch('collect_data.fetch_with_retry') as mock_fetch:
            mock_fetch.return_value = {'ok': True}
            result = fetch_astronomy_moon('ID', 'SECRET', timeout=5, max_retries=2)
        self.assertEqual(result, {'ok': True})
        self.assertIn('moon-phase', mock_fetch.call_args[0][0])
        self.assertEqual(mock_fetch.call_args[1]['method'], 'POST')
        self.assertEqual(mock_fetch.call_args[1]['headers']['Authorization'][:6], 'Basic ')
        payload = mock_fetch.call_args[1]['payload']
        self.assertEqual(payload['format'], 'png')
        self.assertEqual(payload['observer']['latitude'], 37.38283)
        self.assertEqual(payload['observer']['longitude'], -5.97317)
        self.assertEqual(payload['observer']['date'], '2026-08-11')
        self.assertEqual(payload['view']['type'], 'portrait-simple')
        self.assertEqual(payload['style'], {
            'moonStyle': 'default',
            'backgroundStyle': 'stars',
            'backgroundColor': 'black',
            'headingColor': 'white',
            'textColor': 'white',
        })
        self.assertNotIn('elevation', payload['observer'])
        self.assertEqual(mock_fetch.call_args[1]['label'], 'AstronomyAPI moon')

    def test_fetch_astronomy_star_chart_posts_payload_with_date_and_string_style(self):
        with patch('collect_data.astronomy_now', return_value=FIXED_NOW), \
                patch('collect_data.fetch_with_retry') as mock_fetch:
            mock_fetch.return_value = {'ok': True}
            result = fetch_astronomy_star_chart('ID', 'SECRET', timeout=5, max_retries=2)
        self.assertEqual(result, {'ok': True})
        self.assertIn('star-chart', mock_fetch.call_args[0][0])
        self.assertEqual(mock_fetch.call_args[1]['method'], 'POST')
        payload = mock_fetch.call_args[1]['payload']
        self.assertEqual(payload['observer']['longitude'], -5.97317)
        self.assertEqual(payload['observer']['date'], '2026-08-11')
        self.assertIsInstance(payload['style'], str)
        self.assertIn(payload['style'], ('navy', 'inverted'))
        self.assertIsInstance(payload['view'], dict)
        self.assertNotIn('elevation', payload['observer'])
        self.assertEqual(mock_fetch.call_args[1]['label'], 'AstronomyAPI star-chart')


class TestCollectReal(unittest.TestCase):
    def setUp(self):
        self.fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def _raw(self, name):
        with open(os.path.join(self.fixture_dir, name), 'r') as f:
            return json.load(f)

    def _all_ok_patches(self):
        return (
            patch('collect_data.fetch_apod', return_value=self._raw('nasa-apod-image.json')),
            patch('collect_data.fetch_neo', return_value=self._raw('nasa-neo.json')),
            patch('collect_data.fetch_astronomy_positions', return_value=self._raw('astronomy-positions.json')),
            patch('collect_data.fetch_astronomy_moon', return_value=self._raw('astronomy-moon.json')),
            patch('collect_data.fetch_astronomy_star_chart', return_value=self._raw('astronomy-star-chart.json')),
            patch('collect_data.collect_ephemerides', return_value=0),
        )

    def _enter(self, patches):
        stack = ExitStack()
        for item in patches:
            stack.enter_context(item)
        return stack

    def test_collect_real_writes_all_datasets(self):
        with self._enter(self._all_ok_patches()):
            code = collect_real(self.data_dir, 'KEY', 'ID', 'SECRET')
        self.assertEqual(code, 0)
        for name in ('apod.json', 'near-earth.json', 'sky-today.json', 'moon.json', 'star-chart.json'):
            path = os.path.join(self.data_dir, name)
            self.assertTrue(os.path.exists(path), name)
            with open(path, 'r') as f:
                dataset = json.load(f)
            self.assertEqual(dataset['status'], 'live')
            self.assertEqual(validate_dataset(name, dataset), [])
        with open(os.path.join(self.data_dir, 'moon.json'), 'r') as f:
            moon = json.load(f)
        self.assertEqual(
            moon['image_url'],
            'https://widgets.astronomyapi.com/moon-phase/generated/20260811.png'
        )
        self.assertEqual(moon['phase'], 'Waxing Gibbous')
        self.assertEqual(moon['illumination'], 0.78)

    def test_collect_real_preserves_existing_on_failure(self):
        existing = {
            'source': 'NASA APOD',
            'fetched_at': '2026-01-01T00:00:00+00:00',
            'status': 'live',
            'media_type': 'image',
            'url': 'https://example.com/old.png',
        }
        path = os.path.join(self.data_dir, 'apod.json')
        with open(path, 'w') as f:
            json.dump(existing, f)

        patches = list(self._all_ok_patches())
        patches[0] = patch('collect_data.fetch_apod', return_value=None)
        with self._enter(patches):
            code = collect_real(self.data_dir, 'KEY', 'ID', 'SECRET')

        self.assertEqual(code, 1)
        with open(path, 'r') as f:
            self.assertEqual(json.load(f), existing)
        self.assertTrue(os.path.exists(os.path.join(self.data_dir, 'near-earth.json')))

    def test_collect_real_moon_keeps_previous_when_positions_unavailable(self):
        existing = {
            'source': 'AstronomyAPI',
            'fetched_at': '2026-01-01T00:00:00+00:00',
            'status': 'live',
            'phase': 'Gibosa creciente',
            'illumination': 0.5,
            'distance_km': 378500.0,
            'image_url': 'https://widgets.astronomyapi.com/moon-phase/generated/old.png',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317, 'elevation': 0, 'label': 'Sevilla'},
        }
        path = os.path.join(self.data_dir, 'moon.json')
        with open(path, 'w') as f:
            json.dump(existing, f)

        patches = list(self._all_ok_patches())
        patches[2] = patch('collect_data.fetch_astronomy_positions', return_value=None)
        with self._enter(patches):
            code = collect_real(self.data_dir, 'KEY', 'ID', 'SECRET')

        self.assertEqual(code, 1)
        with open(path, 'r') as f:
            self.assertEqual(json.load(f), existing)
        self.assertTrue(os.path.exists(os.path.join(self.data_dir, 'apod.json')))

    def test_collect_real_no_write_on_validation_failure(self):
        patches = list(self._all_ok_patches())
        patches[0] = patch('collect_data.fetch_apod', return_value={'junk': True})
        with self._enter(patches):
            code = collect_real(self.data_dir, 'KEY', 'ID', 'SECRET')
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(os.path.join(self.data_dir, 'apod.json')))
        self.assertTrue(os.path.exists(os.path.join(self.data_dir, 'near-earth.json')))

    def test_collect_real_dry_run_writes_nothing(self):
        with self._enter(self._all_ok_patches()):
            code = collect_real(self.data_dir, 'KEY', 'ID', 'SECRET', write=False)
        self.assertEqual(code, 0)
        self.assertEqual(os.listdir(self.data_dir), [])

    def test_collect_real_nonzero_on_ephemerides_degraded(self):
        """collect_real should return non-zero when collect_ephemerides returns 2 (degraded),
        but should still preserve previous ephemerides.json."""
        existing = {
            'status': 'live',
            'fetched_at': '2026-01-01T00:00:00+00:00',
            'target_date': '2026-01-01',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317, 'label': 'Sevilla'},
            'observation_window': {'start_local': '2026-01-01T00:00+01:00', 'end_local': '2026-01-02T12:00+01:00'},
            'events': [{'id': 'old-event', 'type': 'other', 'title_es': 'Old', 'summary_es': '',
                        'start_local': '2026-01-01T20:00+01:00',
                        'visibility': {'status': 'visible', 'label': 'V', 'reason': 'R'},
                        'source': {'name': 'X', 'url': 'https://example.com'}}],
            'weather': {},
            'sources': [{'name': 'In-The-Sky', 'url': 'https://in-the-sky.org/'}],
        }
        eph_path = os.path.join(self.data_dir, 'ephemerides.json')
        with open(eph_path, 'w') as f:
            json.dump(existing, f)

        # Mock collect_ephemerides to return 2 (degraded preservation)
        patches = list(self._all_ok_patches())
        patches[-1] = patch('collect_data.collect_ephemerides', return_value=2)
        with self._enter(patches):
            code = collect_real(self.data_dir, 'KEY', 'ID', 'SECRET')

        self.assertEqual(code, 1)  # Non-zero overall result
        # Previous ephemerides.json should be preserved
        with open(eph_path, 'r') as f:
            data = json.load(f)
        self.assertEqual(data, existing)
        # Other datasets should still be written
        self.assertTrue(os.path.exists(os.path.join(self.data_dir, 'apod.json')))
        self.assertTrue(os.path.exists(os.path.join(self.data_dir, 'near-earth.json')))


class TestWritePreviewDatasets(unittest.TestCase):
    def test_write_preview_writes_five_marked_files(self):
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        with tempfile.TemporaryDirectory() as tmp:
            code = write_preview_datasets(tmp, fixtures_dir=fixtures_dir)
            self.assertEqual(code, 0)
            for name in ('apod.json', 'near-earth.json', 'sky-today.json', 'moon.json', 'star-chart.json'):
                path = os.path.join(tmp, name)
                self.assertTrue(os.path.exists(path), name)
                with open(path, 'r') as f:
                    dataset = json.load(f)
                self.assertEqual(dataset['status'], 'preview')
                self.assertEqual(validate_dataset(name, dataset), [])


class TestMain(unittest.TestCase):
    def test_main_missing_credentials_returns_nonzero(self):
        with patch.dict(os.environ, {}, clear=True), patch('collect_data.write_preview_datasets') as mock_fix:
            code = main(['--data-dir', 'ignored'])
        self.assertEqual(code, 1)
        mock_fix.assert_not_called()

    def test_main_fixtures_flag(self):
        with patch('collect_data.write_preview_datasets', return_value=0) as mock_fix:
            code = main(['--fixtures', '--data-dir', 'some-dir'])
        self.assertEqual(code, 0)
        mock_fix.assert_called_once_with('some-dir')


if __name__ == '__main__':
    unittest.main()
