import argparse
import base64
import http.client
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

try:
    import astronomy as _astronomy
except ImportError:
    _astronomy = None


OBSERVER_LATITUDE = 37.38283
OBSERVER_LONGITUDE = -5.97317
OBSERVER_ELEVATION = 0
OBSERVER_LABEL = "Sevilla"
OBSERVER_TIMEZONE = ZoneInfo("Europe/Madrid")

NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
NASA_NEO_URL = "https://api.nasa.gov/neo/rest/v1/feed"
ASTRONOMY_API_URL = "https://api.astronomyapi.com/api/v2"
LAUNCH_LIBRARY_UPCOMING_URL = "https://ll.thespacedevs.com/2.3.0/launches/upcoming/"

DATA_FILE_NAMES = ("apod.json", "sky-today.json", "moon.json", "star-chart.json", "near-earth.json", "ephemerides.json", "launches.json")

EPHEMERIDES_ICS_URL = "https://in-the-sky.org/newscalyear_ical.php?year={year}&maxdiff=7"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
MYMEMORY_URL = "https://api.mymemory.translated.net/get"

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def astronomy_now() -> datetime:
    return datetime.now(OBSERVER_TIMEZONE)


def target_date_for(now: Optional[datetime] = None) -> 'datetime.date':
    """Return civil tomorrow of Sevilla: now.astimezone(Europe/Madrid).date() + 1 day."""
    if now is None:
        now = datetime.now(OBSERVER_TIMEZONE)
    else:
        now = now.astimezone(OBSERVER_TIMEZONE)
    return (now + timedelta(days=1)).date()


def astronomy_time_from_datetime(dt: datetime) -> Any:
    """Convert a timezone-aware datetime to an astronomy.Time object."""
    if _astronomy is None:
        raise ImportError(
            'astronomy-engine is required for ephemerides computation. '
            'Install it with: pip install astronomy-engine==2.1.19'
        )
    utc = dt.astimezone(timezone.utc)
    return _astronomy.Time.Make(utc.year, utc.month, utc.day,
                                utc.hour, utc.minute, utc.second)


def lunar_phase_name_from_angle(phase_degrees: float) -> str:
    """Return the conventional English phase name for a Moon phase angle.

    Astronomy Engine uses 0° = new moon, 90° = first quarter,
    180° = full moon, 270° = last quarter.
    """
    phase = float(phase_degrees) % 360.0
    names = (
        'New Moon', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous',
        'Full Moon', 'Waning Gibbous', 'Last Quarter', 'Waning Crescent'
    )
    return names[int(((phase + 22.5) % 360) // 45)]


def lunar_phase_from_datetime(aware_dt: datetime) -> Dict[str, Any]:
    """Calculate trustworthy Moon phase metadata with Astronomy Engine."""
    if _astronomy is None:
        raise ImportError(
            'astronomy-engine is required for lunar phase computation. '
            'Install it with: pip install astronomy-engine==2.1.19'
        )
    time_obj = astronomy_time_from_datetime(aware_dt)
    phase_degrees = float(_astronomy.MoonPhase(time_obj))
    illumination = (1.0 - math.cos(math.radians(phase_degrees))) / 2.0
    return {
        'phase': lunar_phase_name_from_angle(phase_degrees),
        'phase_degrees': phase_degrees,
        'illumination': illumination,
    }


def horizontal_coordinates(body_name: str, aware_dt: datetime,
                           observer: Any = None) -> Dict[str, float]:
    """Compute horizontal coordinates (altitude, azimuth) for a body using Astronomy Engine.

    Returns dict with altitude_deg, azimuth_deg, and sun_altitude_deg.
    """
    if _astronomy is None:
        raise ImportError(
            'astronomy-engine is required for horizontal coordinates. '
            'Install it with: pip install astronomy-engine==2.1.19'
        )
    body_map = {
        'Sun': _astronomy.Body.Sun,
        'Moon': _astronomy.Body.Moon,
        'Mercury': _astronomy.Body.Mercury,
        'Venus': _astronomy.Body.Venus,
        'Mars': _astronomy.Body.Mars,
        'Jupiter': _astronomy.Body.Jupiter,
        'Saturn': _astronomy.Body.Saturn,
        'Uranus': _astronomy.Body.Uranus,
        'Neptune': _astronomy.Body.Neptune,
    }
    body = body_map.get(body_name)
    if body is None:
        raise ValueError(f'Unknown body: {body_name}')

    if observer is None:
        observer = _astronomy.Observer(OBSERVER_LATITUDE, OBSERVER_LONGITUDE, OBSERVER_ELEVATION)

    time = astronomy_time_from_datetime(aware_dt)
    equ = _astronomy.Equator(body, time, observer, True, True)
    hor = _astronomy.Horizon(time, observer, equ.ra, equ.dec, _astronomy.Refraction.Normal)

    sun_equ = _astronomy.Equator(_astronomy.Body.Sun, time, observer, True, True)
    sun_hor = _astronomy.Horizon(time, observer, sun_equ.ra, sun_equ.dec, _astronomy.Refraction.Normal)

    return {
        'altitude_deg': hor.altitude,
        'azimuth_deg': hor.azimuth,
        'sun_altitude_deg': sun_hor.altitude,
    }


BODY_NAME_MAP_ES = {
    'Sun': 'Sol',
    'Moon': 'Luna',
    'Mercury': 'Mercurio',
    'Venus': 'Venus',
    'Mars': 'Marte',
    'Jupiter': 'Júpiter',
    'Saturn': 'Saturno',
    'Uranus': 'Urano',
    'Neptune': 'Neptuno',
}

CONSTELLATION_NAME_MAP_ES = {
    'Aries': 'Aries',
    'Taurus': 'Tauro',
    'Gemini': 'Géminis',
    'Cancer': 'Cáncer',
    'Leo': 'León',
    'Virgo': 'Virgo',
    'Libra': 'Libra',
    'Scorpius': 'Escorpio',
    'Sagittarius': 'Sagitario',
    'Capricornus': 'Capricornio',
    'Aquarius': 'Acuario',
    'Pisces': 'Piscis',
    'Orion': 'Orión',
    'Centaurus': 'Centaurus',
    'Cygnus': 'Cisne',
    'Cassiopeia': 'Casiopea',
    'Ursa Mayor': 'Osa Mayor',
    'Ursa Minor': 'Osa Menor',
    'Ophiuchus': 'Ofiuco',
    'Hercules': 'Hércules',
    'Lyra': 'Lira',
    'Andromeda': 'Andrómeda',
    'Pegasus': 'Pegaso',
    'Cetus': 'Cetus',
    'Eridanus': 'Eridano',
    'Hydra': 'Hidra',
    'Corvus': 'Cuervo',
    'Crux': 'Cruz',
    'Carina': 'Quilla',
    'Vela': 'Vela',
    'Puppis': 'Popa',
    'Lupus': 'Lobo',
    'Ara': 'Ara',
    'Triangulum': 'Triángulo',
    'Perseus': 'Perseo',
    'Auriga': 'Auriga',
    'Boötes': 'Boyeros',
    'Corona Borealis': 'Corona Boreal',
    'Serpens': 'Serpiente',
    'Scutum': 'Escudo',
    'Sagitta': 'Flecha',
    'Delphinus': 'Delfín',
    'Equuleus': 'Equuleo',
    'Piscis Austrinus': 'Piscis Austral',
    'Grus': 'Grulla',
    'Phoenix': 'Fénix',
    'Tucana': 'Tucán',
    'Indus': 'Indio',
    'Octans': 'Octante',
    'Musca': 'Mosca',
    'Chamaeleon': 'Camaleón',
    'Reticulum': 'Reticulante',
    'Horologium': 'Reloj',
    'Eridanus (Achernar)': 'Eridano',
    'Pavo': 'Pavo',
    'Volans': 'Volante',
    'Sculptor': 'Escultor',
    'Fornax': 'Horno',
    'Caelum': 'Cincel',
    'Columba': 'Paloma',
    'Lepus': 'Liebre',
    'Monoceros': 'Monoceros',
    'Canis Minor': 'Can Menor',
    'Canis Major': 'Can Mayor',
    'Gemini (Castor)': 'Géminis',
}


def _translate_body_name(name: str) -> str:
    return BODY_NAME_MAP_ES.get(name, name)


def _translate_constellation(name: str) -> str:
    return CONSTELLATION_NAME_MAP_ES.get(name, name)


BODY_NAMES = {
    'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune',
}


def assess_visibility(body_name: str, altitude_deg: float,
                      sun_altitude_deg: float) -> Dict[str, str]:
    """Assess visibility for a celestial body based on altitude and Sun position.

    Rules:
    - Solar events: visible if altitude >= 0° (Sun above horizon), with protection required
    - Non-solar identifiable bodies: visible if altitude >= 10° and Sun <= -6°
    - Below horizon (altitude < 0): not_visible
    - Daylight (Sun altitude >= -6°): not_visible/contextual
    - Non-identifiable events: uncertain/contextual
    """
    is_solar = body_name == 'Sun'

    if altitude_deg < 0:
        return {
            'status': 'not_visible',
            'label': 'Bajo el horizonte',
            'reason': f'{_translate_body_name(body_name)} está bajo el horizonte '
                      f'(altitud {altitude_deg:.1f}°).',
        }

    if is_solar:
        # For solar events (eclipses), the body IS the Sun.
        # Use altitude_deg (which equals sun_altitude_deg for the Sun).
        # Eclipse is visible when Sun is above horizon.
        if altitude_deg >= 0:
            return {
                'status': 'visible',
                'label': 'Visible con protección',
                'reason': 'Eclipse solar visible. Usar gafas de eclipse homologadas (norma ISO 12312-2).',
            }
        else:
            return {
                'status': 'not_visible',
                'label': 'Bajo el horizonte',
                'reason': f'El Sol está bajo el horizonte (altitud {altitude_deg:.1f}°).',
            }

    if not is_solar and body_name in BODY_NAMES:
        if altitude_deg >= 10 and sun_altitude_deg <= -6:
            return {
                'status': 'visible',
                'label': 'Visible',
                'reason': f'{_translate_body_name(body_name)} observable sobre el horizonte en cielo nocturno.',
            }
        else:
            return {
                'status': 'not_visible',
                'label': 'No visible',
                'reason': f'{_translate_body_name(body_name)} no observable: '
                          f'altitud {altitude_deg:.1f}°, Sol a {sun_altitude_deg:.1f}°.',
            }

    return {
        'status': 'uncertain',
        'label': 'Requiere verificación',
        'reason': 'No se pudo determinar visibilidad automáticamente.',
    }


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


def normalize_apod(raw: Dict[str, Any],
                    translator: Optional[Callable[[str], Tuple[str, str]]] = None) -> Dict[str, Any]:
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

    if translator is None:
        translator = translate_text_mymemory

    title = raw.get('title', '')
    explanation = raw.get('explanation', '')
    if title:
        title_es, t_status = translator(title)
        normalized['title_es'] = title_es
        normalized['title_translation_status'] = t_status
    if explanation:
        exp_es, e_status = translator(explanation)
        normalized['explanation_es'] = exp_es
        normalized['explanation_translation_status'] = e_status

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
        if str(body_meta.get('id', '')).lower() == 'earth':
            continue
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

    position_date = moon_position.get('date')
    if position_date:
        phase_dt = datetime.fromisoformat(str(position_date))
    else:
        phase_dt = astronomy_now()

    calculated_phase = lunar_phase_from_datetime(phase_dt)

    distance_km = moon_position.get('distance', {}).get('fromEarth', {}).get('km')
    if distance_km is None:
        raise ValueError("AstronomyAPI moon row missing distance.fromEarth.km")

    normalized = {
        'source': 'AstronomyAPI + Astronomy Engine',
        'fetched_at': _now_iso(),
        'status': 'live',
        'phase': calculated_phase['phase'],
        'phase_degrees': round(calculated_phase['phase_degrees'], 3),
        'illumination': round(calculated_phase['illumination'], 6),
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



def normalize_launches(raw: Dict[str, Any], max_items: int = 8) -> Dict[str, Any]:
    if 'results' not in raw or not isinstance(raw['results'], list):
        raise ValueError("Launch Library payload missing required results list")
    launches = []
    for item in raw['results'][:max_items]:
        if not isinstance(item, dict):
            continue
        mission = item.get('mission') or {}
        rocket = item.get('rocket') or {}
        configuration = rocket.get('configuration') or {}
        pad = item.get('pad') or {}
        location = pad.get('location') or {}
        status = item.get('status') or {}
        agency = item.get('launch_service_provider') or {}
        image = item.get('image') or {}
        launch = {
            'id': item.get('id') or '',
            'name': item.get('name') or '',
            'net': item.get('net') or '',
            'window_start': item.get('window_start') or '',
            'window_end': item.get('window_end') or '',
            'status': status.get('name') or '',
            'status_abbrev': status.get('abbrev') or '',
            'agency': agency.get('name') or '',
            'rocket': configuration.get('full_name') or configuration.get('name') or '',
            'mission': mission.get('name') or '',
            'mission_description': mission.get('description') or '',
            'pad': pad.get('name') or '',
            'location': location.get('name') or '',
            'image_url': image.get('image_url') if isinstance(image, dict) else '',
            'webcast_url': item.get('webcast_live') or '',
            'url': item.get('url') or '',
        }
        if launch['name'] and launch['net']:
            launches.append(launch)
    return {
        'source': 'The Space Devs Launch Library 2',
        'fetched_at': _now_iso(),
        'status': 'live',
        'count': raw.get('count', len(launches)),
        'launches': launches,
    }

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


def validate_ephemerides(dataset: Dict[str, Any]) -> List[str]:
    errors = []
    for field in ('status', 'fetched_at', 'target_date', 'timezone', 'observer',
                   'observation_window', 'events', 'weather', 'sources'):
        if field not in dataset or dataset.get(field) in (None, ''):
            errors.append(field)
    if 'observer' in dataset and isinstance(dataset['observer'], dict):
        obs = dataset['observer']
        for field in ('latitude', 'longitude'):
            if field not in obs:
                errors.append('observer.{}'.format(field))
    if 'target_date' in dataset and isinstance(dataset['target_date'], str):
        try:
            parts = dataset['target_date'].split('-')
            datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            errors.append('target_date.invalid_format')
    if 'timezone' in dataset and dataset['timezone'] != 'Europe/Madrid':
        errors.append('timezone.wrong_value')
    window = dataset.get('observation_window')
    if isinstance(window, dict):
        for wf in ('start_local', 'end_local'):
            if wf not in window:
                errors.append('observation_window.{}'.format(wf))
        start = window.get('start_local', '')
        end = window.get('end_local', '')
        if start and end and start >= end:
            errors.append('observation_window.out_of_order')
    events = dataset.get('events')
    if isinstance(events, list):
        valid_event_types = (
            'solar_eclipse', 'lunar_eclipse', 'meteor_shower', 'conjunction', 'opposition',
            'lunar_phase', 'planet_visible', 'comet',
            'asteroid_close', 'iss_pass', 'other',
        )
        seen_ids = set()
        for idx, event in enumerate(events):
            for field in ('id', 'type', 'title_es', 'summary_es', 'start_local',
                           'visibility', 'source'):
                if field not in event:
                    errors.append('events[{}].{}'.format(idx, field))
            if 'type' in event and event['type'] not in valid_event_types:
                errors.append('events[{}].invalid_type'.format(idx))
            vis = event.get('visibility', {})
            vis_status = vis.get('status', '')
            allowed = ('visible', 'contextual', 'uncertain', 'not_visible')
            if vis_status and vis_status not in allowed:
                errors.append('events[{}].visibility.status'.format(idx))
            if 'label' not in vis:
                errors.append('events[{}].visibility.label'.format(idx))
            if 'reason' not in vis:
                errors.append('events[{}].visibility.reason'.format(idx))
            src = event.get('source', {})
            url = src.get('url', '')
            if url and not url.startswith('https://'):
                errors.append('events[{}].source.url'.format(idx))
            # Check for duplicate event IDs
            event_id = event.get('id')
            if event_id:
                if event_id in seen_ids:
                    errors.append('events[{}].id.duplicate'.format(idx))
                else:
                    seen_ids.add(event_id)
    status = dataset.get('status')
    sources = dataset.get('sources')
    if status == 'live' and isinstance(sources, list) and len(sources) == 0:
        errors.append('sources.empty_for_live')
    return errors


def validate_launches(dataset: Dict[str, Any]) -> List[str]:
    errors = _missing_meta(dataset)
    launches = dataset.get('launches')
    if not isinstance(launches, list):
        return errors + ['launches']
    for index, launch in enumerate(launches):
        for field in ('name', 'net'):
            if not launch.get(field):
                errors.append('launches[{}].{}'.format(index, field))
    return errors


VALIDATORS: Dict[str, Callable[[Dict[str, Any]], List[str]]] = {
    'apod.json': validate_apod,
    'near-earth.json': validate_neo,
    'sky-today.json': validate_positions,
    'moon.json': validate_moon,
    'star-chart.json': validate_star_chart,
    'ephemerides.json': validate_ephemerides,
    'launches.json': validate_launches,
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
        except (urllib.error.URLError, TimeoutError, ConnectionError,
                http.client.IncompleteRead, http.client.RemoteDisconnected):
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


def build_launches_url(limit: int = 8) -> str:
    params = {'format': 'json', 'limit': limit, 'mode': 'normal', 'ordering': 'net'}
    return LAUNCH_LIBRARY_UPCOMING_URL + '?' + urllib.parse.urlencode(params)


def fetch_launches(timeout: int = 10, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    return fetch_with_retry(build_launches_url(), timeout=timeout, max_retries=max_retries,
                            label='Launch Library 2')


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


def unfold_ics_lines(raw_text: str) -> List[str]:
    """Unfold ICS folded lines (RFC 5545: lines starting with space are continuations)."""
    lines = raw_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    result = []
    for line in lines:
        if line.startswith(' ') and result:
            result[-1] += line[1:]
        else:
            result.append(line)
    return result


def parse_ics_events(raw_text: str, target_year: int) -> List[Dict[str, Any]]:
    """Parse an ICS calendar and return event dicts for the target year.

    Validates that the response is a plausible VCALENDAR with at least one VEVENT.
    Returns empty list for non-VCALENDAR content (e.g., HTML error pages).
    """
    lines = unfold_ics_lines(raw_text)

    # Validate the calendar envelope and VEVENT nesting before parsing fields.
    content_lines = [line for line in lines if line.strip()]
    markers = [line.strip() for line in content_lines]
    if (not content_lines or markers[0] != 'BEGIN:VCALENDAR'
            or markers[-1] != 'END:VCALENDAR'
            or markers.count('BEGIN:VCALENDAR') != 1
            or markers.count('END:VCALENDAR') != 1):
        return []

    component_stack = []
    saw_event = False
    for line in content_lines:
        marker = line.strip()
        if marker.startswith('BEGIN:'):
            component = marker[6:]
            if component == 'VCALENDAR':
                if component_stack:
                    return []
            elif not component_stack:
                return []
            if component == 'VEVENT':
                if component_stack != ['VCALENDAR']:
                    return []
                saw_event = True
            component_stack.append(component)
        elif marker.startswith('END:'):
            component = marker[4:]
            if not component_stack or component_stack[-1] != component:
                return []
            component_stack.pop()

    if component_stack or not saw_event:
        return []

    events = []
    in_event = False
    current: Dict[str, Any] = {}

    for line in lines:
        if line == 'BEGIN:VEVENT':
            in_event = True
            current = {}
        elif line == 'END:VEVENT':
            in_event = False
            if current.get('dtstart'):
                events.append(current)
            current = {}
        elif in_event:
            if ':' in line:
                key, _, value = line.partition(':')
                key_lower = key.split(';')[0].strip()
                if key_lower == 'DTSTART':
                    current['dtstart'] = value.strip()
                elif key_lower == 'SUMMARY':
                    current['summary'] = value.strip()
                elif key_lower == 'DESCRIPTION':
                    current['description'] = value.strip()
                elif key_lower == 'URL':
                    current['url'] = value.strip()
                elif key_lower == 'UID':
                    current['uid'] = value.strip()

    filtered = []
    for ev in events:
        ds = ev.get('dtstart', '')
        if len(ds) >= 4 and ds[:4] == str(target_year):
            filtered.append(ev)
    return filtered


def fetch_ics_events(year: int, timeout: int = 10, max_retries: int = 3) -> Optional[str]:
    """Fetch the annual ICS calendar from in-the-sky.org."""
    url = EPHEMERIDES_ICS_URL.format(year=year)
    request_headers = {'User-Agent': 'AstroAIDA/1.0'}
    req = urllib.request.Request(url, headers=request_headers)
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.getcode() == 200:
                    return resp.read().decode('utf-8', errors='replace')
                if resp.getcode() in (429, 502, 503, 504) and attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                print('[astroaida] ephemerides ICS: HTTP {}'.format(resp.getcode()))
                return None
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                http.client.IncompleteRead, http.client.RemoteDisconnected) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (429, 502, 503, 504):
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            print('[astroaida] ephemerides ICS: network error')
            return None
        except Exception:
            print('[astroaida] ephemerides ICS: unexpected error')
            return None
    print('[astroaida] ephemerides ICS: max retries exceeded')
    return None


def civil_morning(target_date: 'datetime.date', tz: ZoneInfo) -> datetime:
    """Calculate civil morning (dawn) for a given date in Europe/Madrid using Astronomy Engine.

    Uses SearchRiseSet to find when the Sun rises, then subtracts ~36 minutes for
    civil twilight (Sun ~6° below horizon). Falls back to an approximate offset if
    astronomy-engine is unavailable.
    """
    if _astronomy is None:
        dt = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=tz)
        hour_offset = 5
        if target_date.month in (11, 12, 1):
            hour_offset = 7
        elif target_date.month in (2, 10):
            hour_offset = 6
        elif target_date.month in (3, 4, 8, 9):
            hour_offset = 5
        else:
            hour_offset = 4
        return dt.replace(hour=hour_offset, minute=0)

    observer = _astronomy.Observer(OBSERVER_LATITUDE, OBSERVER_LONGITUDE, OBSERVER_ELEVATION)
    dt_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=tz)
    time_start = astronomy_time_from_datetime(dt_start)
    dt_end = datetime.combine(target_date + timedelta(days=1), datetime.min.time()).replace(tzinfo=tz)
    time_end = astronomy_time_from_datetime(dt_end)

    try:
        rise_time = _astronomy.SearchRiseSet(_astronomy.Body.Sun, observer,
                                              _astronomy.Direction.Rise,
                                              time_start, 2)
        if rise_time is not None:
            rise_utc = rise_time.Utc().replace(tzinfo=timezone.utc)
            rise_local = rise_utc.astimezone(tz)
            civil_dawn = rise_local - timedelta(minutes=36)
            return civil_dawn.replace(second=0, microsecond=0)
    except Exception:
        pass

    dt = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=tz)
    hour_offset = 5
    if target_date.month in (11, 12, 1):
        hour_offset = 7
    elif target_date.month in (2, 10):
        hour_offset = 6
    elif target_date.month in (3, 4, 8, 9):
        hour_offset = 5
    else:
        hour_offset = 4
    return dt.replace(hour=hour_offset, minute=0)


def observation_window(target_date: 'datetime.date', tz: ZoneInfo) -> Tuple[datetime, datetime]:
    """Return (start_local, end_local) window: target_date 00:00 to next day 12:00."""
    start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=tz)
    next_date = target_date + timedelta(days=1)
    end = datetime.combine(next_date, datetime.min.time()).replace(hour=12, tzinfo=tz)
    return start, end


def fetch_weather_open_meteo(target_date: str, lat: float = OBSERVER_LATITUDE,
                              lon: float = OBSERVER_LONGITUDE,
                              timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Fetch weather forecast from Open-Meteo for target_date and next day using hourly data.

    Returns summary of nighttime hours only (cloud_cover, visibility, precipitation_probability, temperature),
    strictly filtered to the observation window: target_date 00:00 Europe/Madrid to next day 12:00.
    """
    from datetime import date as _date_type
    parts = target_date.split('-')
    td = _date_type(int(parts[0]), int(parts[1]), int(parts[2]))
    next_date = (td + timedelta(days=1)).isoformat()

    params = {
        'latitude': lat,
        'longitude': lon,
        'hourly': 'cloud_cover,visibility,precipitation_probability,temperature_2m',
        'start_date': target_date,
        'end_date': next_date,
        'timezone': 'Europe/Madrid',
    }
    url = OPEN_METEO_URL + '?' + urllib.parse.urlencode(params)
    result = fetch_with_retry(url, timeout=timeout, max_retries=2, label='Open-Meteo weather')
    if not result or 'hourly' not in result:
        return None

    hourly = result['hourly']
    times = hourly.get('time', [])
    cloud = hourly.get('cloud_cover', [])
    vis = hourly.get('visibility', [])
    precip = hourly.get('precipitation_probability', [])
    temp = hourly.get('temperature_2m', [])

    tz_madrid = ZoneInfo('Europe/Madrid')
    window_start = datetime.combine(td, datetime.min.time()).replace(tzinfo=tz_madrid)
    window_end = datetime.combine(td + timedelta(days=1), datetime.min.time()).replace(hour=12, tzinfo=tz_madrid)

    night_hours = []
    for i, t_str in enumerate(times):
        try:
            dt = datetime.fromisoformat(t_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz_madrid)

            # Strictly filter to observation window
            if not (window_start <= dt <= window_end):
                continue

            try:
                is_dark = horizontal_coordinates('Sun', dt)['sun_altitude_deg'] <= -6.0
            except (ImportError, ValueError):
                # Conservative fallback only when Astronomy Engine is unavailable.
                is_dark = dt.hour < 7 or dt.hour >= 21
            if is_dark:
                night_hours.append({
                    'cloud_cover': cloud[i] if i < len(cloud) else None,
                    'visibility': vis[i] if i < len(vis) else None,
                    'precipitation_probability': precip[i] if i < len(precip) else None,
                    'temperature': temp[i] if i < len(temp) else None,
                })
        except (ValueError, TypeError):
            continue

    if not night_hours:
        return {}

    weather: Dict[str, Any] = {}
    cloud_vals = [h['cloud_cover'] for h in night_hours if h['cloud_cover'] is not None]
    if cloud_vals:
        weather['cloud_cover'] = sum(cloud_vals) / len(cloud_vals)

    vis_vals = [h['visibility'] for h in night_hours if h['visibility'] is not None]
    if vis_vals:
        weather['visibility'] = max(vis_vals)

    precip_vals = [h['precipitation_probability'] for h in night_hours if h['precipitation_probability'] is not None]
    if precip_vals:
        weather['precipitation_probability'] = max(precip_vals)

    temp_vals = [h['temperature'] for h in night_hours if h['temperature'] is not None]
    if temp_vals:
        weather['temperature'] = round(sum(temp_vals) / len(temp_vals), 1)

    return weather


def translate_text_mymemory(text: str, langpair: str = 'en|es',
                             timeout: int = 5) -> Tuple[str, str]:
    """Translate text server-side using bounded MyMemory requests.

    Returns ``translated``, ``partial`` or ``unavailable`` without discarding
    the original text when the provider fails.
    """
    if not text or not text.strip():
        return text, 'unavailable'

    max_chunk = 450
    chunks: List[str] = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current = ''
    for sentence in sentences:
        while len(sentence) > max_chunk:
            if current:
                chunks.append(current)
                current = ''
            split_at = sentence.rfind(' ', 0, max_chunk + 1)
            if split_at < 1:
                split_at = max_chunk
            chunks.append(sentence[:split_at].strip())
            sentence = sentence[split_at:].strip()
        if len(current) + len(sentence) + 1 <= max_chunk:
            current = (current + ' ' + sentence).strip()
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)

    translated_parts: List[str] = []
    successful_parts = 0
    for chunk in chunks:
        params = urllib.parse.urlencode({'langpair': langpair, 'q': chunk})
        result = fetch_with_retry(MYMEMORY_URL + '?' + params, timeout=timeout,
                                  max_retries=1, label='MyMemory')
        translated = None
        if result and result.get('responseStatus') == 200:
            translated = result.get('responseData', {}).get('translatedText')
        if translated and translated.strip() and translated.strip() != chunk.strip():
            translated_parts.append(translated.strip())
            successful_parts += 1
        else:
            translated_parts.append(chunk)

    if successful_parts == len(chunks):
        status = 'translated'
    elif successful_parts:
        status = 'partial'
    else:
        status = 'unavailable'
    return ' '.join(translated_parts), status


def title_es_from_ics(summary: str) -> str:
    """Generate a short Spanish title from an ICS event summary.

    Returns deterministic Spanish for known event types.
    For unknown events, returns the original summary as fallback (no hybrid translations).
    """
    mapping = {
        'solar eclipse': 'Eclipse solar',
        'lunar eclipse': 'Eclipse lunar',
        'meteor shower': 'Lluvia de meteoros',
        'conjunction': 'Conjunción',
        'opposition': 'Oposición',
        'quadrature': 'Cuadratura',
        'perihelion': 'Perihelio',
        'aphelion': 'Afelio',
        'solstice': 'Solsticio',
        'equinox': 'Equinoccio',
        'full moon': 'Luna llena',
        'new moon': 'Luna nueva',
        'first quarter': 'Cuarto creciente',
        'last quarter': 'Cuarto menguante',
    }
    lower = summary.lower()
    for eng, esp in mapping.items():
        if eng in lower:
            return esp

    # For unknown events, return original summary as fallback (no hybrid translations)
    # The caller can mark translation_status as 'unavailable' if needed
    return summary[:80]


def _body_from_summary(summary: str) -> Optional[str]:
    """Return an Astronomy Engine body name mentioned in a short event title."""
    aliases = {
        'sun': 'Sun', 'sol': 'Sun', 'moon': 'Moon', 'luna': 'Moon',
        'mercury': 'Mercury', 'mercurio': 'Mercury', 'venus': 'Venus',
        'mars': 'Mars', 'marte': 'Mars', 'jupiter': 'Jupiter', 'júpiter': 'Jupiter',
        'saturn': 'Saturn', 'saturno': 'Saturn', 'uranus': 'Uranus', 'urano': 'Uranus',
        'neptune': 'Neptune', 'neptuno': 'Neptune',
    }
    lower = summary.lower()
    for alias, body in aliases.items():
        if re.search(r'\b{}\b'.format(re.escape(alias)), lower):
            return body
    return None


def _generate_event_id(ics_event: Dict[str, Any], target_date: 'datetime.date') -> str:
    """Generate a stable, collision-resistant event ID.

    Priority:
    1. If UID exists: use a sanitized version of it
    2. Otherwise: deterministic hash of full DTSTART + full SUMMARY
    """
    import hashlib

    uid = ics_event.get('uid')
    if uid:
        # Keep a readable DOM-safe prefix, but hash the original UID so distinct
        # values cannot collide merely because sanitization removes punctuation.
        safe_uid = re.sub(r'[^a-zA-Z0-9_-]+', '-', uid).strip('-')[:40]
        uid_hash = hashlib.sha256(uid.encode('utf-8')).hexdigest()[:12]
        return '{}-{}-{}'.format(safe_uid or 'uid', uid_hash, target_date.isoformat())

    # No UID: deterministic hash of full DTSTART + full SUMMARY
    dtstart = ics_event.get('dtstart', '')
    summary = ics_event.get('summary', '')
    combined = '{}|{}'.format(dtstart, summary)
    hash_suffix = hashlib.sha256(combined.encode('utf-8')).hexdigest()[:12]
    # Also include a readable prefix from summary for debugging
    readable_prefix = re.sub(r'[^a-z0-9]+', '-', summary[:30].lower()).strip('-')
    return '{}-{}-{}'.format(readable_prefix or 'event', hash_suffix, target_date.isoformat())


def build_ephemerides_event(ics_event: Dict[str, Any], target_date: 'datetime.date',
                             tz: ZoneInfo) -> Dict[str, Any]:
    """Build a localized event and verify identifiable bodies from Sevilla."""
    raw_summary = ics_event.get('summary', '')
    start_local = _parse_ics_dtstart(ics_event.get('dtstart', ''), tz)
    event_type = _classify_ics_event(raw_summary)
    title_es = title_es_from_ics(raw_summary)
    title_translation_status = 'deterministic'
    if title_es == raw_summary[:80]:
        translated_title, translated_status = translate_text_mymemory(raw_summary[:80])
        if translated_status == 'translated':
            title_es = translated_title
            title_translation_status = 'translated'
        else:
            # Preserve the intact source title instead of publishing a hybrid translation.
            title_translation_status = 'unavailable'

    summary_es = ''
    desc = ics_event.get('description', '')
    if desc:
        clean_desc = re.sub(r'https?://\S+', '', desc[:240]).strip(' .')
        if clean_desc:
            summary_es, _ = translate_text_mymemory(clean_desc)

    event_id = _generate_event_id(ics_event, target_date)
    source_url = ics_event.get('url', 'https://in-the-sky.org/')
    if not source_url.startswith('https://'):
        source_url = 'https://in-the-sky.org/'

    if event_type == 'lunar_phase' and 'new moon' in raw_summary.lower():
        visibility = {
            'status': 'contextual',
            'label': 'No observable directamente',
            'reason': 'La Luna nueva no se ve, pero favorece un cielo nocturno más oscuro.',
        }
    else:
        body_name = _body_from_summary(raw_summary)
        if body_name and start_local:
            try:
                coords = horizontal_coordinates(body_name, datetime.fromisoformat(start_local))
                visibility = assess_visibility(body_name, coords['altitude_deg'],
                                               coords['sun_altitude_deg'])
                visibility.update({
                    'altitude_deg': round(coords['altitude_deg'], 1),
                    'azimuth_deg': round(coords['azimuth_deg'], 1),
                    'sun_altitude_deg': round(coords['sun_altitude_deg'], 1),
                })
            except (ImportError, ValueError):
                visibility = {
                    'status': 'uncertain',
                    'label': 'Visibilidad no verificada',
                    'reason': 'No se pudo calcular su posición local con Astronomy Engine.',
                }
        else:
            visibility = {
                'status': 'contextual',
                'label': 'Acontecimiento astronómico',
                'reason': 'El catálogo no aporta un objeto único cuya altura pueda verificarse.',
            }

    return {
        'id': event_id,
        'type': event_type,
        'title_es': title_es,
        'title_translation_status': title_translation_status,
        'summary_es': summary_es,
        'start_local': start_local,
        'visibility': visibility,
        'source': {'name': 'In-The-Sky', 'url': source_url},
    }


def _parse_ics_dtstart(dtstart: str, tz: ZoneInfo) -> str:
    """Parse ICS DTSTART to ISO local string."""
    match = re.match(r'(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z?', dtstart)
    if match:
        y, m, d, H, M, S = match.groups()
        if dtstart.endswith('Z'):
            dt = datetime(int(y), int(m), int(d), int(H), int(M), int(S), tzinfo=timezone.utc)
            dt_local = dt.astimezone(tz)
        else:
            dt_local = datetime(int(y), int(m), int(d), int(H), int(M), int(S), tzinfo=tz)
        return dt_local.isoformat()
    match_date = re.match(r'(\d{4})(\d{2})(\d{2})', dtstart)
    if match_date:
        y, m, d = match_date.groups()
        dt_local = datetime(int(y), int(m), int(d), 12, 0, 0, tzinfo=tz)
        return dt_local.isoformat()
    return dtstart


def _classify_ics_event(summary: str) -> str:
    """Classify an ICS event into a type string."""
    lower = summary.lower()
    if 'solar eclipse' in lower:
        return 'solar_eclipse'
    if 'lunar eclipse' in lower:
        return 'lunar_eclipse'
    if 'meteor' in lower or 'shower' in lower:
        return 'meteor_shower'
    if 'conjunction' in lower:
        return 'conjunction'
    if 'opposition' in lower:
        return 'opposition'
    if 'perihelion' in lower or 'aphelion' in lower:
        return 'other'
    if 'solstice' in lower or 'equinox' in lower:
        return 'other'
    if 'moon' in lower and 'new' in lower:
        return 'lunar_phase'
    if 'moon' in lower and 'full' in lower:
        return 'lunar_phase'
    if 'quarter' in lower:
        return 'lunar_phase'
    return 'other'


def build_special_events(target_date: 'datetime.date', tz: ZoneInfo,
                          weather: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build special events like the 2026-08-12 solar eclipse and Perseids."""
    events = []
    if target_date == target_date.replace(year=2026, month=8, day=12):
        eclipse_event = _build_eclipse_event_2026(target_date, tz)
        if eclipse_event:
            events.append(eclipse_event)

    if target_date.year == 2026 and target_date.month == 8 and target_date.day in (12, 13):
        events.append({
            'id': 'perseids-2026-08-12',
            'type': 'meteor_shower',
            'title_es': 'Perseidas 2026',
            'summary_es': (
                'Lluvia de meteoros Perseidas. Máximo aproximado madrugada del 13 de agosto, '
                'entre las 04:00 y las 06:00 hora local (según IGN). '
                'Luna nueva favorable (poca interferencia lunar). '
                'Sujeto a condiciones meteorológicas.'
            ),
            'start_local': '2026-08-13T04:00:00+02:00',
            'visibility': {
                'status': 'uncertain',
                'label': 'Dependiente del tiempo',
                'reason': (
                    'Máximo nocturno; verifique nubosidad y contaminación lumínica. '
                    'Luna nueva favorable.'
                ),
                'radiant': 'Perseus',
                'moon_phase': 'Luna nueva (favorable)',
            },
            'source': {
                'name': 'IGN',
                'url': 'https://www.ign.es/web/ign/portal/last-catalog-articles/-/article/lloveras-de-meteoros',
            },
        })

    return events


def _build_eclipse_event_2026(target_date: 'datetime.date', tz: ZoneInfo) -> Optional[Dict[str, Any]]:
    """Build the 2026-08-12 solar eclipse event using Astronomy Engine."""
    if _astronomy is None:
        return _eclipse_event_fallback(target_date, tz, reason='astronomy-engine not available')

    observer = _astronomy.Observer(OBSERVER_LATITUDE, OBSERVER_LONGITUDE, OBSERVER_ELEVATION)
    search_time = astronomy_time_from_datetime(
        datetime(target_date.year, target_date.month, 1, 0, 0, 0, tzinfo=tz)
    )

    try:
        eclipse = _astronomy.SearchLocalSolarEclipse(search_time, observer)
    except Exception:
        return _eclipse_event_fallback(target_date, tz, reason='SearchLocalSolarEclipse failed')

    if eclipse is None:
        return _eclipse_event_fallback(target_date, tz, reason='no eclipse found in range')

    partial_begin_utc = eclipse.partial_begin.time.Utc().replace(tzinfo=timezone.utc)
    partial_begin_local = partial_begin_utc.astimezone(tz)
    peak_utc = eclipse.peak.time.Utc().replace(tzinfo=timezone.utc)
    peak_local = peak_utc.astimezone(tz)
    partial_end_utc = eclipse.partial_end.time.Utc().replace(tzinfo=timezone.utc)
    partial_end_local = partial_end_utc.astimezone(tz)

    if partial_begin_local.date() != target_date:
        return _eclipse_event_fallback(target_date, tz, reason='eclipse not on target date')

    obscuration = eclipse.obscuration
    is_total = eclipse.kind == _astronomy.EclipseKind.Total

    if is_total:
        title_es = 'Eclipse solar total'
        magnitude_text = 'total'
    else:
        title_es = 'Eclipse solar parcial'
        magnitude_text = f'parcial, con una ocultación del {obscuration:.1%}'

    summary_es = (
        f'Eclipse solar {magnitude_text} desde Sevilla. '
        f'Inicio parcial {partial_begin_local.strftime("%H:%M")} hora local y '
        f'máximo {peak_local.strftime("%H:%M")}. '
        f'El final geométrico es a las {partial_end_local.strftime("%H:%M")}, '
        'cuando el Sol ya está bajo el horizonte; solo puede observarse mientras permanezca visible. '
        'Protección ocular homologada obligatoria durante toda la observación.'
    )

    peak_alt = eclipse.peak.altitude

    return {
        'id': 'solar-eclipse-partial-2026-08-12',
        'type': 'solar_eclipse',
        'title_es': title_es,
        'summary_es': summary_es,
        'start_local': partial_begin_local.isoformat(),
        'end_local': partial_end_local.isoformat(),
        'peak_local': peak_local.isoformat(),
        'peak_altitude_deg': round(peak_alt, 2),
        'obscuration': round(obscuration, 4),
        'is_total_from_location': is_total,
        'visibility': {
            'status': 'visible',
            'label': 'Visible con protección',
            'reason': (
                'Eclipse parcial desde Sevilla. Usar gafas de eclipse homologadas '
                '(norma ISO 12312-2). No observar sin protección.'
            ),
            'type': 'solar_eclipse',
            'magnitude': magnitude_text,
            'protection_required': True,
            'official_links': [
                'https://visualizadores.ign.es/eclipses/2026',
                'https://eclipse.gsfc.nasa.gov/SEsearch/SEsearchmap.php?Ecl=20260812',
            ],
        },
        'source': {
            'name': 'Astronomy Engine + IGN',
            'url': 'https://visualizadores.ign.es/eclipses/2026',
        },
    }


def _eclipse_event_fallback(target_date: 'datetime.date', tz: ZoneInfo,
                             reason: str = '') -> Optional[Dict[str, Any]]:
    """Fallback eclipse event if Astronomy Engine is unavailable."""
    if target_date != target_date.replace(year=2026, month=8, day=12):
        return None
    return {
        'id': 'solar-eclipse-partial-2026-08-12',
        'type': 'solar_eclipse',
        'title_es': 'Eclipse solar parcial',
        'summary_es': (
            'Eclipse solar parcial visible desde Sevilla al atardecer. '
            'La Luna cubrirá parte del disco solar. '
            'Protección ocular homologada obligatoria durante toda la observación. '
            'Más información: https://visualizadores.ign.es/eclipses/2026 y '
            'https://eclipse.gsfc.nasa.gov/SEsearch/SEsearchmap.php?Ecl=20260812'
        ),
        'start_local': '2026-08-12T19:41:00+02:00',
        'visibility': {
            'status': 'uncertain',
            'label': 'Cálculo no disponible',
            'reason': (
                f'Fallback: {reason}. '
                'Eclipse parcial desde Sevilla. Usar gafas de eclipse homologadas '
                '(norma ISO 12312-2). No observar sin protección.'
            ),
            'type': 'solar_eclipse',
            'magnitude': 'parcial',
            'protection_required': True,
            'official_links': [
                'https://visualizadores.ign.es/eclipses/2026',
                'https://eclipse.gsfc.nasa.gov/SEsearch/SEsearchmap.php?Ecl=20260812',
            ],
        },
        'source': {
            'name': 'IGN (fallback)',
            'url': 'https://visualizadores.ign.es/eclipses/2026',
        },
    }


def _ics_event_in_window(ics_event: Dict[str, Any],
                          window_start: datetime,
                          window_end: datetime,
                          tz: ZoneInfo) -> bool:
    """Check if an ICS event's DTSTART falls within the observation window."""
    dtstart = ics_event.get('dtstart', '')
    try:
        local_iso = _parse_ics_dtstart(dtstart, tz)
        event_dt = datetime.fromisoformat(local_iso)
        return window_start <= event_dt <= window_end
    except (ValueError, TypeError):
        return False


def normalize_ephemerides(ics_events: List[Dict[str, Any]],
                           target_date: 'datetime.date',
                           tz: ZoneInfo,
                           weather: Optional[Dict[str, Any]],
                           special_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize ephemerides data into the final JSON schema."""
    window_start, window_end = observation_window(target_date, tz)

    filtered_ics = [ev for ev in ics_events
                    if _ics_event_in_window(ev, window_start, window_end, tz)]

    has_special_eclipse = any(event.get('type') == 'solar_eclipse' for event in special_events)
    has_special_perseids = any(event.get('id', '').startswith('perseids-') for event in special_events)
    events = []
    for ics_ev in filtered_ics:
        summary_lower = ics_ev.get('summary', '').lower()
        if has_special_eclipse and 'solar eclipse' in summary_lower:
            continue
        if has_special_perseids and 'perseid' in summary_lower:
            continue
        events.append(build_ephemerides_event(ics_ev, target_date, tz))

    events.extend(special_events)

    events.sort(key=lambda e: e.get('start_local', ''))

    # Deterministic deduplication by event ID: keep first occurrence
    seen_ids = set()
    deduped_events = []
    for event in events:
        event_id = event.get('id')
        if event_id and event_id not in seen_ids:
            seen_ids.add(event_id)
            deduped_events.append(event)
        elif not event_id:
            # Events without ID are kept (should not happen in practice)
            deduped_events.append(event)
    events = deduped_events

    return {
        'source': 'In-The-Sky / Open-Meteo',
        'fetched_at': _now_iso(),
        'status': 'live',
        'target_date': target_date.isoformat(),
        'timezone': tz.key,
        'observer': {
            'latitude': OBSERVER_LATITUDE,
            'longitude': OBSERVER_LONGITUDE,
            'label': OBSERVER_LABEL,
        },
        'observation_window': {
            'start_local': window_start.isoformat(),
            'end_local': window_end.isoformat(),
        },
        'events': events,
        'weather': weather if weather else {},
        'sources': [
            {'name': 'In-The-Sky', 'url': 'https://in-the-sky.org/'},
            {'name': 'Open-Meteo', 'url': 'https://open-meteo.com/'},
            {'name': 'IGN', 'url': 'https://www.ign.es/'},
            {'name': 'MyMemory', 'url': 'https://www.translated.net/MyMemory/'},
        ],
    }


def collect_ephemerides(data_dir: str, timeout: int = 10, write: bool = True,
                          target_date_override: Optional['datetime.date'] = None) -> int:
    """Collect ephemerides from ICS + Open-Meteo + special events.

    Returns:
        0: Complete success (ICS fetched, validated, written)
        1: Hard failure (no ICS and no previous data, or validation failed, or write failed)
        2: Degraded preservation (ICS unavailable but previous data preserved)
    """
    tz = OBSERVER_TIMEZONE
    now = astronomy_now()
    if target_date_override is not None:
        target_date = target_date_override
    else:
        target_date = target_date_for(now)

    ics_raw = fetch_ics_events(year=target_date.year, timeout=timeout)
    ics_events = []
    if ics_raw:
        ics_events = parse_ics_events(ics_raw, target_date.year)
        if not ics_events:
            print('[astroaida] ephemerides: ICS returned content but parsed zero events (invalid/unavailable)')
            eph_path = os.path.join(data_dir, 'ephemerides.json')
            if os.path.exists(eph_path):
                print('[astroaida] ephemerides: preserving previous ephemerides.json (degraded)')
                return 2
            else:
                print('[astroaida] ephemerides: no previous data and ICS invalid; cannot generate')
                return 1
        print('[astroaida] ephemerides: parsed {} ICS events for {}'.format(
            len(ics_events), target_date.year))
    else:
        print('[astroaida] ephemerides: ICS unavailable')
        eph_path = os.path.join(data_dir, 'ephemerides.json')
        if os.path.exists(eph_path):
            print('[astroaida] ephemerides: preserving previous ephemerides.json (degraded)')
            return 2
        else:
            print('[astroaida] ephemerides: no previous data and ICS unavailable; cannot generate')
            return 1

    weather = fetch_weather_open_meteo(target_date.isoformat(), timeout=timeout)
    if weather:
        print('[astroaida] ephemerides: weather data fetched')
    else:
        print('[astroaida] ephemerides: weather unavailable')

    special = build_special_events(target_date, tz, weather)

    dataset = normalize_ephemerides(ics_events, target_date, tz, weather, special)

    errors = validate_ephemerides(dataset)
    if errors:
        print('[astroaida] ephemerides.json: validation errors {}; keeping previous data'.format(errors))
        return 1

    if not write:
        print('[astroaida] ephemerides.json: valid (dry run, not writing)')
        return 0

    try:
        write_json_atomically(os.path.join(data_dir, 'ephemerides.json'), dataset)
        print('[astroaida] wrote ephemerides.json')
    except Exception as exc:
        print('[astroaida] ephemerides.json: write failed ({}); keeping previous data'.format(exc))
        return 1

    return 0


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
                 timeout: int = 10, max_retries: int = 3, write: bool = True,
                 target_date_override: Optional['datetime.date'] = None) -> int:
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
        'apod.json': (fetch_results['apod'],
                      lambda raw: normalize_apod(raw, translator=translate_text_mymemory)),
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

    eph_code = collect_ephemerides(data_dir, timeout=timeout, write=write,
                                     target_date_override=target_date_override)
    if eph_code == 1:
        failures += 1
    elif eph_code == 2:
        print('[astroaida] WARNING: ephemerides degraded preservation (ICS unavailable, using cached data)')
        failures += 1

    return 1 if failures else 0


def _noop_translator(text: str) -> Tuple[str, str]:
    """No-op translator for fixture/preview mode. Returns original text as unavailable."""
    return text, 'unavailable'


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
        'apod.json': ('nasa-apod-image.json', lambda raw: normalize_apod(raw, translator=_noop_translator)),
        'near-earth.json': ('nasa-neo.json', normalize_neo),
        'sky-today.json': ('astronomy-positions.json', normalize_astronomy_positions),
        'moon.json': ('astronomy-moon.json', lambda raw: normalize_astronomy_moon(positions_raw, raw)),
        'star-chart.json': ('astronomy-star-chart.json', normalize_star_chart),
    }

    preview_launches = {
        'source': 'The Space Devs Launch Library 2',
        'fetched_at': _now_iso(),
        'status': 'preview',
        'count': 1,
        'launches': [{
            'id': 'preview-starlink',
            'name': 'Falcon 9 Block 5 | Starlink Group de muestra',
            'net': (datetime.now(timezone.utc) + timedelta(days=2)).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
            'window_start': '', 'window_end': '', 'status': 'To Be Confirmed', 'status_abbrev': 'TBC',
            'agency': 'SpaceX', 'rocket': 'Falcon 9 Block 5', 'mission': 'Starlink',
            'mission_description': 'Lanzamiento de muestra para validar la sección de eventos espaciales.',
            'pad': 'Complejo de lanzamiento de muestra', 'location': 'Florida, Estados Unidos',
            'image_url': '', 'webcast_url': '', 'url': 'https://ll.thespacedevs.com/2.3.0/launches/upcoming/'
        }]
    }
    failures = 0
    if not validate_dataset('launches.json', preview_launches):
        try:
            write_json_atomically(os.path.join(data_dir, 'launches.json'), preview_launches)
            print('[astroaida] wrote preview launches.json')
        except Exception as exc:
            print('[astroaida] launches.json: write failed ({})'.format(exc))
            failures += 1

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

    eph_fixture = os.path.join(fixtures_dir, 'ephemerides.json')
    if os.path.exists(eph_fixture):
        try:
            with open(eph_fixture, 'r', encoding='utf-8') as f:
                eph_data = json.load(f)
            eph_data['status'] = 'preview'
            eph_errors = validate_ephemerides(eph_data)
            if eph_errors:
                print('[astroaida] ephemerides.json: preview validation errors {}'.format(eph_errors))
                failures += 1
            else:
                write_json_atomically(os.path.join(data_dir, 'ephemerides.json'), eph_data)
                print('[astroaida] wrote preview ephemerides.json')
        except Exception as exc:
            print('[astroaida] ephemerides.json: preview failed ({}); keeping previous data'.format(exc))
            failures += 1
    else:
        print('[astroaida] ephemerides.json: no fixture found; generating default')
        tz = OBSERVER_TIMEZONE
        now = astronomy_now()
        target = target_date_for(now)
        window_start, window_end = observation_window(target, tz)
        special = build_special_events(target, tz, None)
        dataset = {
            'source': 'In-The-Sky / Open-Meteo',
            'fetched_at': _now_iso(),
            'status': 'preview',
            'target_date': target.isoformat(),
            'timezone': tz.key,
            'observer': {
                'latitude': OBSERVER_LATITUDE,
                'longitude': OBSERVER_LONGITUDE,
                'label': OBSERVER_LABEL,
            },
            'observation_window': {
                'start_local': window_start.isoformat(),
                'end_local': window_end.isoformat(),
            },
            'events': special,
            'weather': {},
            'sources': [
                {'name': 'In-The-Sky', 'url': 'https://in-the-sky.org/'},
                {'name': 'Open-Meteo', 'url': 'https://open-meteo.com/'},
                {'name': 'IGN', 'url': 'https://www.ign.es/'},
            ],
        }
        eph_errors = validate_ephemerides(dataset)
        if eph_errors:
            print('[astroaida] ephemerides.json: default validation errors {}'.format(eph_errors))
            failures += 1
        else:
            try:
                write_json_atomically(os.path.join(data_dir, 'ephemerides.json'), dataset)
                print('[astroaida] wrote default ephemerides.json')
            except Exception as exc:
                print('[astroaida] ephemerides.json: write failed ({})'.format(exc))
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
    parser.add_argument('--target-date', default=None,
                        help='Override target date (YYYY-MM-DD) for ephemerides collection.')
    args = parser.parse_args(argv)

    target_date_override = None
    if args.target_date:
        parts = args.target_date.split('-')
        target_date_override = datetime(int(parts[0]), int(parts[1]), int(parts[2])).date()

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

    code = collect_real(args.data_dir, nasa_key, astronomy_id, astronomy_secret,
                        write=not args.dry_run, target_date_override=target_date_override)
    if args.dry_run:
        print('[astroaida] Dry run finished; no files were written.')
    return code


if __name__ == '__main__':
    sys.exit(main())
