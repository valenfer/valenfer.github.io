import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional
from zoneinfo import ZoneInfo


OBSERVER_LATITUDE = 37.38283
OBSERVER_LONGITUDE = -5.97317
OBSERVER_ELEVATION = 0
OBSERVER_LABEL = "Sevilla"
OBSERVER_TIMEZONE = ZoneInfo("Europe/Madrid")

NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
NASA_NEO_URL = "https://api.nasa.gov/neo/rest/v1/feed"
ASTRONOMY_API_URL = "https://api.astronomyapi.com/api/v2"

DATA_FILE_NAMES = ("apod.json", "sky-today.json", "moon.json", "star-chart.json", "near-earth.json")

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def astronomy_now() -> datetime:
    return datetime.now(OBSERVER_TIMEZONE)


LABEL_FALLBACK = 'fetch'


def _safe_label(label: Optional[str]) -> str:
    if not label:
        return LABEL_FALLBACK
    safe = re.sub(r'[^A-Za-z0-9 _-]', '', label).strip()
    return safe or LABEL_FALLBACK


def _build_observer(meta_observer: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    observer = meta_observer or {}
    return {
        'latitude': observer.get('latitude', OBSERVER_LATITUDE),
        'longitude': observer.get('longitude', OBSERVER_LONGITUDE),
        'elevation': observer.get('elevation', OBSERVER_ELEVATION),
        'label': OBSERVER_LABEL,
    }


def normalize_apod(raw: Dict[str, Any]) -> Dict[str, Any]:
    if 'media_type' not in raw:
        raise ValueError("APOD missing required field: media_type")
    if 'url' not in raw:
        raise ValueError("APOD missing required field: url")

    normalized = {
        'media_type': raw['media_type'],
        'url': raw['url'],
        'title': raw.get('title', ''),
        'explanation': raw.get('explanation', ''),
        'date': raw.get('date', ''),
        'source': 'NASA APOD',
        'fetched_at': _now_iso(),
        'status': 'live',
    }

    if 'copyright' in raw and raw['copyright']:
        normalized['copyright'] = raw['copyright']

    return normalized


def normalize_neo(raw: Dict[str, Any]) -> Dict[str, Any]:
    if 'near_earth_objects' not in raw:
        raise ValueError("NeoWs feed missing required field: near_earth_objects")

    asteroids = []
    for date_str, neo_list in raw['near_earth_objects'].items():
        for neo in neo_list:
            close_approach = neo['close_approach_data'][0] if neo.get('close_approach_data') else {}
            relative_velocity = close_approach.get('relative_velocity', {})
            miss_distance = close_approach.get('miss_distance', {})

            asteroid = {
                'date': date_str,
                'name': neo.get('name', ''),
                'estimated_diameter_km': {
                    'min': neo.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_min', 0),
                    'max': neo.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_max', 0)
                },
                'miss_distance_km': int(float(miss_distance.get('kilometers', 0))),
                'velocity_km_s': float(relative_velocity.get('kilometers_per_second', 0)),
                'hazardous': neo.get('is_potentially_hazardous_asteroid', False),
                'nasa_url': neo.get('nasa_jpl_url', '')
            }
            asteroids.append(asteroid)

    return {
        'source': 'NASA NeoWs',
        'fetched_at': _now_iso(),
        'status': 'live',
        'asteroids': asteroids
    }


def normalize_astronomy_positions(raw: Dict[str, Any]) -> Dict[str, Any]:
    if 'data' not in raw or 'rows' not in raw['data']:
        raise ValueError("AstronomyAPI positions missing required data.rows structure")

    bodies = []
    for row in raw['data']['rows']:
        body_meta = row.get('body', {})
        positions = row.get('positions')
        if not positions:
            continue
        position = positions[0]
        body_position = position.get('position', {})
        horizontal = body_position.get('horizontal', {})
        altitude_degrees = horizontal.get('altitude', {}).get('degrees')
        azimuth_degrees = horizontal.get('azimuth', {}).get('degrees')
        distance_km = position.get('distance', {}).get('fromEarth', {}).get('km')
        constellation = body_position.get('constellation', {}).get('name')
        if altitude_degrees is None or azimuth_degrees is None or distance_km is None:
            raise ValueError("AstronomyAPI positions row missing altitude/azimuth/distance fields")

        body = {
            'name': body_meta.get('name', '') or position.get('name', ''),
            'altitude': float(altitude_degrees),
            'azimuth': float(azimuth_degrees),
            'constellation': constellation or '',
            'distance_km': float(distance_km),
        }
        extra_info = position.get('extraInfo', {})
        if extra_info.get('magnitude') is not None:
            body['magnitude'] = float(extra_info['magnitude'])
        phase = extra_info.get('phase') or {}
        if phase.get('string') is not None:
            body['phase'] = phase['string']
        if phase.get('fraction') is not None:
            body['illumination'] = float(phase['fraction'])
        bodies.append(body)

    observer = _build_observer(raw.get('data', {}).get('observer', {}).get('location'))

    return {
        'source': 'AstronomyAPI',
        'fetched_at': _now_iso(),
        'status': 'live',
        'bodies': bodies,
        'observer': observer,
    }


def normalize_astronomy_moon(positions_raw: Optional[Dict[str, Any]],
                             moon_phase_raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not positions_raw or 'data' not in positions_raw or 'rows' not in positions_raw['data']:
        raise ValueError("AstronomyAPI moon requires positions data.rows structure")
    if not moon_phase_raw or 'data' not in moon_phase_raw or 'imageUrl' not in moon_phase_raw['data']:
        raise ValueError("AstronomyAPI moon phase missing required data.imageUrl")

    moon_position = None
    for row in positions_raw['data']['rows']:
        if row.get('body', {}).get('id') == 'moon':
            positions = row.get('positions')
            if positions:
                moon_position = positions[0]
            break
    if moon_position is None:
        raise ValueError("AstronomyAPI positions missing moon row")

    extra_info = moon_position.get('extraInfo', {})
    phase = extra_info.get('phase', {})
    if not phase.get('string') or 'fraction' not in phase:
        raise ValueError("AstronomyAPI moon row missing phase string/fraction")

    distance_km = moon_position.get('distance', {}).get('fromEarth', {}).get('km')
    if distance_km is None:
        raise ValueError("AstronomyAPI moon row missing distance.fromEarth.km")

    normalized = {
        'source': 'AstronomyAPI',
        'fetched_at': _now_iso(),
        'status': 'live',
        'phase': phase['string'],
        'illumination': float(phase['fraction']),
        'distance_km': float(distance_km),
        'image_url': moon_phase_raw['data']['imageUrl'],
    }

    normalized['observer'] = _build_observer(
        positions_raw.get('data', {}).get('observer', {}).get('location'))

    return normalized


def normalize_star_chart(raw: Dict[str, Any]) -> Dict[str, Any]:
    if 'data' not in raw:
        raise ValueError("AstronomyAPI star chart missing required data field")

    data = raw['data']
    if 'imageUrl' not in data:
        raise ValueError("AstronomyAPI star chart missing required field: imageUrl")

    normalized = {
        'source': 'AstronomyAPI',
        'fetched_at': _now_iso(),
        'status': 'live',
        'image_url': data['imageUrl'],
    }

    normalized['observer'] = _build_observer(data.get('observer'))

    return normalized


def _missing_meta(dataset: Dict[str, Any]) -> List[str]:
    return [field for field in ('source', 'fetched_at', 'status')
            if not dataset.get(field)]


def validate_apod(dataset: Dict[str, Any]) -> List[str]:
    errors = _missing_meta(dataset)
    if dataset.get('media_type') not in ('image', 'video'):
        errors.append('media_type')
    if not dataset.get('url'):
        errors.append('url')
    return errors


def validate_neo(dataset: Dict[str, Any]) -> List[str]:
    errors = _missing_meta(dataset)
    asteroids = dataset.get('asteroids')
    if not isinstance(asteroids, list):
        return errors + ['asteroids']
    for index, asteroid in enumerate(asteroids):
        for field in ('date', 'name', 'miss_distance_km', 'velocity_km_s', 'hazardous', 'nasa_url'):
            if field not in asteroid:
                errors.append('asteroids[{}].{}'.format(index, field))
    return errors


def validate_positions(dataset: Dict[str, Any]) -> List[str]:
    errors = _missing_meta(dataset)
    if not isinstance(dataset.get('bodies'), list):
        errors.append('bodies')
    if not isinstance(dataset.get('observer'), dict):
        errors.append('observer')
    return errors


def validate_moon(dataset: Dict[str, Any]) -> List[str]:
    errors = _missing_meta(dataset)
    if not dataset.get('phase'):
        errors.append('phase')
    if not dataset.get('image_url'):
        errors.append('image_url')
    if not isinstance(dataset.get('observer'), dict):
        errors.append('observer')
    return errors


def validate_star_chart(dataset: Dict[str, Any]) -> List[str]:
    errors = _missing_meta(dataset)
    if not dataset.get('image_url'):
        errors.append('image_url')
    return errors


VALIDATORS: Dict[str, Callable[[Dict[str, Any]], List[str]]] = {
    'apod.json': validate_apod,
    'near-earth.json': validate_neo,
    'sky-today.json': validate_positions,
    'moon.json': validate_moon,
    'star-chart.json': validate_star_chart,
}


def validate_dataset(filename: str, dataset: Dict[str, Any]) -> List[str]:
    return VALIDATORS[filename](dataset)


def build_apod_url(api_key: str) -> str:
    params = {'api_key': api_key, 'thumbs': 'true'}
    return NASA_APOD_URL + '?' + urllib.parse.urlencode(params)


def build_neo_url(api_key: str, days: int = 7) -> str:
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)
    params = {
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
        'api_key': api_key,
    }
    return NASA_NEO_URL + '?' + urllib.parse.urlencode(params)


def astronomy_headers(app_id: str, app_secret: str) -> Dict[str, str]:
    token = base64.b64encode('{}:{}'.format(app_id, app_secret).encode('utf-8')).decode('ascii')
    return {'Authorization': 'Basic ' + token}


def fetch_with_retry(url: str, timeout: int = 10, max_retries: int = 3,
                     method: str = 'GET', headers: Optional[Dict[str, str]] = None,
                     payload: Optional[Dict[str, Any]] = None,
                     label: Optional[str] = None) -> Optional[Dict[str, Any]]:
    transient_codes = {429, 502, 503, 504}
    source = _safe_label(label)

    for attempt in range(max_retries + 1):
        try:
            request_headers = {'User-Agent': 'AstroAIDA/1.0'}
            if headers:
                request_headers.update(headers)
            body = None
            if payload is not None:
                body = json.dumps(payload).encode('utf-8')
                request_headers.setdefault('Content-Type', 'application/json')
            req = urllib.request.Request(url, data=body, headers=request_headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                code = response.getcode()
                if code == 200:
                    data = response.read()
                    return json.loads(data.decode('utf-8'))
                if code in transient_codes and attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                print('[astroaida] {}: HTTP {}'.format(source, code))
                return None
        except urllib.error.HTTPError as e:
            if e.code in transient_codes and attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            print('[astroaida] {}: HTTP {}'.format(source, e.code))
            return None
        except urllib.error.URLError:
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            print('[astroaida] {}: network error'.format(source))
            return None
        except json.JSONDecodeError:
            print('[astroaida] {}: invalid JSON'.format(source))
            return None
        except Exception:
            print('[astroaida] {}: unexpected client error'.format(source))
            return None
    print('[astroaida] {}: unexpected client error'.format(source))
    return None


def fetch_apod(api_key: str, timeout: int = 10, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    return fetch_with_retry(build_apod_url(api_key), timeout=timeout, max_retries=max_retries,
                            label='NASA APOD')


def fetch_neo(api_key: str, timeout: int = 10, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    return fetch_with_retry(build_neo_url(api_key), timeout=timeout, max_retries=max_retries,
                            label='NASA NeoWs')


def fetch_astronomy_positions(app_id: str, app_secret: str, timeout: int = 10,
                              max_retries: int = 3) -> Optional[Dict[str, Any]]:
    now = astronomy_now()
    params = {
        'latitude': OBSERVER_LATITUDE,
        'longitude': OBSERVER_LONGITUDE,
        'elevation': OBSERVER_ELEVATION,
        'from_date': now.strftime('%Y-%m-%d'),
        'to_date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M:%S'),
        'output': 'rows',
    }
    url = ASTRONOMY_API_URL + '/bodies/positions?' + urllib.parse.urlencode(params)
    return fetch_with_retry(url, timeout=timeout, max_retries=max_retries,
                            headers=astronomy_headers(app_id, app_secret),
                            label='AstronomyAPI positions')


def fetch_astronomy_moon(app_id: str, app_secret: str, timeout: int = 10,
                         max_retries: int = 3) -> Optional[Dict[str, Any]]:
    today = astronomy_now().strftime('%Y-%m-%d')
    payload = {
        'format': 'png',
        'style': {
            'moonStyle': 'default',
            'backgroundStyle': 'stars',
            'backgroundColor': 'black',
            'headingColor': 'white',
            'textColor': 'white',
        },
        'observer': {
            'latitude': OBSERVER_LATITUDE,
            'longitude': OBSERVER_LONGITUDE,
            'date': today,
        },
        'view': {'type': 'portrait-simple'},
    }
    url = ASTRONOMY_API_URL + '/studio/moon-phase'
    return fetch_with_retry(url, timeout=timeout, max_retries=max_retries, method='POST',
                            headers=astronomy_headers(app_id, app_secret), payload=payload,
                            label='AstronomyAPI moon')


def fetch_astronomy_star_chart(app_id: str, app_secret: str, timeout: int = 10,
                               max_retries: int = 3) -> Optional[Dict[str, Any]]:
    today = astronomy_now().strftime('%Y-%m-%d')
    payload = {
        'style': 'inverted',
        'observer': {
            'latitude': OBSERVER_LATITUDE,
            'longitude': OBSERVER_LONGITUDE,
            'date': today,
        },
        'view': {
            'type': 'area',
            'parameters': {
                'position': {'equatorial': {'rightAscension': 0, 'declination': 0}},
            },
        },
    }
    url = ASTRONOMY_API_URL + '/studio/star-chart'
    return fetch_with_retry(url, timeout=timeout, max_retries=max_retries, method='POST',
                            headers=astronomy_headers(app_id, app_secret), payload=payload,
                            label='AstronomyAPI star-chart')


def write_json_atomically(path: str, data: Dict[str, Any]) -> None:
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    tmp_path = path + '.tmp'
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def collect_real(data_dir: str, nasa_key: str, astronomy_id: str, astronomy_secret: str,
                 timeout: int = 10, max_retries: int = 3, write: bool = True) -> int:
    fetch_results: Dict[str, Any] = {}

    def safe_fetch(name: str, func: Callable[[], Optional[Dict[str, Any]]]) -> None:
        try:
            fetch_results[name] = func()
        except Exception as exc:
            print('[astroaida] {} fetch failed: {}'.format(name, exc))
            fetch_results[name] = None

    safe_fetch('apod', lambda: fetch_apod(nasa_key, timeout, max_retries))
    safe_fetch('near_earth', lambda: fetch_neo(nasa_key, timeout, max_retries))
    safe_fetch('sky_today', lambda: fetch_astronomy_positions(astronomy_id, astronomy_secret, timeout, max_retries))
    safe_fetch('moon', lambda: fetch_astronomy_moon(astronomy_id, astronomy_secret, timeout, max_retries))
    safe_fetch('star_chart', lambda: fetch_astronomy_star_chart(astronomy_id, astronomy_secret, timeout, max_retries))

    positions_raw = fetch_results['sky_today']
    builders = {
        'apod.json': (fetch_results['apod'], normalize_apod),
        'near-earth.json': (fetch_results['near_earth'], normalize_neo),
        'sky-today.json': (positions_raw, normalize_astronomy_positions),
        'moon.json': (fetch_results['moon'], lambda raw: normalize_astronomy_moon(positions_raw, raw)),
        'star-chart.json': (fetch_results['star_chart'], normalize_star_chart),
    }

    failures = 0
    for filename, (raw, normalizer) in builders.items():
        if raw is None:
            print('[astroaida] {}: source unavailable; keeping previous data'.format(filename))
            failures += 1
            continue
        try:
            dataset = normalizer(raw)
            errors = validate_dataset(filename, dataset)
        except Exception as exc:
            print('[astroaida] {}: invalid payload ({}); keeping previous data'.format(filename, exc))
            failures += 1
            continue
        if errors:
            print('[astroaida] {}: validation errors {}; keeping previous data'.format(filename, errors))
            failures += 1
            continue
        if not write:
            print('[astroaida] {}: valid (dry run, not writing)'.format(filename))
            continue
        try:
            write_json_atomically(os.path.join(data_dir, filename), dataset)
            print('[astroaida] wrote {}'.format(filename))
        except Exception as exc:
            print('[astroaida] {}: write failed ({}); keeping previous data'.format(filename, exc))
            failures += 1

    return 1 if failures else 0


def write_preview_datasets(data_dir: str, fixtures_dir: Optional[str] = None) -> int:
    if fixtures_dir is None:
        fixtures_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    'tests', 'fixtures')

    positions_raw = None
    try:
        with open(os.path.join(fixtures_dir, 'astronomy-positions.json'), 'r', encoding='utf-8') as f:
            positions_raw = json.load(f)
    except Exception as exc:
        print('[astroaida] preview positions fixture unavailable ({}); moon preview skipped'.format(exc))

    fixture_sources = {
        'apod.json': ('nasa-apod-image.json', normalize_apod),
        'near-earth.json': ('nasa-neo.json', normalize_neo),
        'sky-today.json': ('astronomy-positions.json', normalize_astronomy_positions),
        'moon.json': ('astronomy-moon.json', lambda raw: normalize_astronomy_moon(positions_raw, raw)),
        'star-chart.json': ('astronomy-star-chart.json', normalize_star_chart),
    }

    failures = 0
    for filename, (fixture_name, normalizer) in fixture_sources.items():
        path = os.path.join(fixtures_dir, fixture_name)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            dataset = normalizer(raw)
            dataset['status'] = 'preview'
            errors = validate_dataset(filename, dataset)
        except Exception as exc:
            print('[astroaida] {}: preview generation failed ({}); keeping previous data'.format(filename, exc))
            failures += 1
            continue
        if errors:
            print('[astroaida] {}: preview validation errors {}'.format(filename, errors))
            failures += 1
            continue
        try:
            write_json_atomically(os.path.join(data_dir, filename), dataset)
            print('[astroaida] wrote preview {}'.format(filename))
        except Exception as exc:
            print('[astroaida] {}: write failed ({})'.format(filename, exc))
            failures += 1

    return 1 if failures else 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog='collect_data',
        description='Collect and normalize AstroAIDA datasets from NASA and AstronomyAPI.')
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR,
                        help='Directory where normalized JSON datasets are written.')
    parser.add_argument('--fixtures', action='store_true',
                        help='Write preview datasets from bundled test fixtures (no network, no credentials).')
    parser.add_argument('--dry-run', action='store_true',
                        help='Fetch and validate but do not write any files.')
    args = parser.parse_args(argv)

    if args.fixtures:
        return write_preview_datasets(args.data_dir)

    nasa_key = os.environ.get('NASA_API_KEY', '').strip()
    astronomy_id = os.environ.get('ASTRONOMY_APP_ID', '').strip()
    astronomy_secret = os.environ.get('ASTRONOMY_APP_SECRET', '').strip()

    missing = [label for label, value in (
        ('NASA_API_KEY', nasa_key),
        ('ASTRONOMY_APP_ID', astronomy_id),
        ('ASTRONOMY_APP_SECRET', astronomy_secret),
    ) if not value]
    if missing:
        print('[astroaida] Missing required environment variables: ' + ', '.join(missing))
        print('[astroaida] Run with --fixtures to write preview data, or configure credentials via GitHub Secrets.')
        return 1

    code = collect_real(args.data_dir, nasa_key, astronomy_id, astronomy_secret, write=not args.dry_run)
    if args.dry_run:
        print('[astroaida] Dry run finished; no files were written.')
    return code


if __name__ == '__main__':
    sys.exit(main())
