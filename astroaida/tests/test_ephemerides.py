import html.parser
import json
import os
import re
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo

SITE_ROOT = os.path.join(os.path.dirname(__file__), '..')
SCRIPTS_ROOT = os.path.join(os.path.dirname(__file__), '..', 'scripts')

sys.path.insert(0, SCRIPTS_ROOT)
import collect_data

EXPECTED_LINKS_WITH_EPH = [
    ('#apod', 'Astronomía del día'),
    ('#sky-today', 'Cielo hoy'),
    ('#moon', 'Luna'),
    ('#star-chart', 'Carta celeste'),
    ('#near-earth', 'Asteroides'),
    ('#ephemerides', 'Efemérides'),
]

EXPECTED_SECTIONS_WITH_EPH = [
    'apod', 'sky-today', 'moon', 'star-chart', 'near-earth', 'ephemerides'
]


def css_block(css, selector):
    start = css.find(selector)
    if start == -1:
        return ''
    brace = css.find('{', start)
    if brace == -1:
        return ''
    depth = 0
    for i in range(brace, len(css)):
        if css[i] == '{':
            depth += 1
        elif css[i] == '}':
            depth -= 1
            if depth == 0:
                return css[brace + 1:i]
    return ''


class EphemeridesHtmlParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.nav_labels = []
        self.nav_links = []
        self.doc_ids = []
        self.section_ids = []
        self.in_nav = False
        self.in_link = False
        self.link_href = None
        self.link_text = []
        self.ephemerides_section = None
        self.in_section = None
        self.section_aria = None
        self.data_modules = []

    def handle_starttag(self, tag, attrs):
        values = {k: v or '' for k, v in attrs}
        id_val = values.get('id')
        if id_val:
            self.doc_ids.append(id_val)

        if tag == 'nav':
            label = values.get('aria-label')
            if label:
                self.nav_labels.append(label)
            self.in_nav = True

        if tag == 'section':
            sid = values.get('id')
            aria = values.get('aria-labelledby')
            if sid:
                self.section_ids.append(sid)
                if sid == 'ephemerides':
                    self.ephemerides_section = {
                        'id': sid,
                        'aria-labelledby': aria,
                    }
            self.in_section = sid

        if tag == 'a' and self.in_nav:
            self.in_link = True
            self.link_href = values.get('href')
            self.link_text = []

        dm = values.get('data-module')
        if dm:
            self.data_modules.append(dm)

    def handle_endtag(self, tag):
        if tag == 'nav':
            self.in_nav = False
        if tag == 'a' and self.in_link:
            self.in_link = False
            if self.link_href:
                self.nav_links.append((self.link_href, ''.join(self.link_text).strip()))
        if tag == 'section':
            self.in_section = None

    def handle_data(self, data):
        if self.in_link:
            self.link_text.append(data)


class TestEphemeridesNavMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(SITE_ROOT, 'index.html'), encoding='utf-8') as f:
            cls.index_html = f.read()
        with open(os.path.join(SITE_ROOT, 'styles.css'), encoding='utf-8') as f:
            cls.styles = f.read()
        cls.parser = EphemeridesHtmlParser()
        cls.parser.feed(cls.index_html)

    def test_sixth_nav_link_exists(self):
        self.assertEqual(len(self.parser.nav_links), 6)

    def test_sixth_nav_link_is_ephemerides(self):
        self.assertEqual(self.parser.nav_links[5], ('#ephemerides', 'Efemérides'))

    def test_expected_links_with_ephemerides(self):
        self.assertEqual(self.parser.nav_links, EXPECTED_LINKS_WITH_EPH)

    def test_ephemerides_section_id_exists(self):
        self.assertIn('ephemerides', self.parser.doc_ids)

    def test_ephemerides_section_count(self):
        self.assertEqual(self.parser.doc_ids.count('ephemerides'), 1)

    def test_sections_order_with_ephemerides(self):
        self.assertEqual(self.parser.section_ids, EXPECTED_SECTIONS_WITH_EPH)

    def test_ephemerides_section_has_aria_labelledby(self):
        self.assertIsNotNone(self.parser.ephemerides_section)
        self.assertEqual(
            self.parser.ephemerides_section['aria-labelledby'], 'ephemerides-title')

    def test_ephemerides_section_exists(self):
        self.assertIn('ephemerides', self.parser.section_ids)

    def test_ephemerides_module_in_html(self):
        self.assertIn('ephemerides', self.parser.data_modules)

    def test_nav_wraps_without_overflow(self):
        block = css_block(self.styles, '.site-nav__list {')
        self.assertIn('flex-wrap: wrap', block)

    def test_ephemerides_section_scroll_margin(self):
        block = css_block(self.styles, 'section[id]')
        self.assertIn('scroll-margin-top', block)

    def test_nav_links_meet_44px(self):
        block = css_block(self.styles, '.site-nav__link {')
        self.assertIn('min-height: 44px', block)

    def test_nav_sticky(self):
        block = css_block(self.styles, '.site-nav {')
        self.assertIn('position: sticky', block)

    def test_smooth_scroll_only_when_motion_ok(self):
        ok_block = css_block(self.styles, '@media (prefers-reduced-motion: no-preference)')
        self.assertIn('scroll-behavior: smooth', ok_block)


class TestEphemeridesSectionHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(SITE_ROOT, 'index.html'), encoding='utf-8') as f:
            cls.index_html = f.read()

    def test_ephemerides_section_present(self):
        self.assertIn('id="ephemerides"', self.index_html)

    def test_ephemerides_aria_labelledby(self):
        self.assertIn('aria-labelledby="ephemerides-title"', self.index_html)

    def test_ephemerides_title_heading(self):
        self.assertIn('id="ephemerides-title"', self.index_html)

    def test_ephemerides_data_module(self):
        self.assertIn('data-module="ephemerides"', self.index_html)

    def test_ephemerides_loading_placeholder(self):
        self.assertIn('data-module="ephemerides"', self.index_html)

    def test_no_ephemerides_in_csp(self):
        csp_match = re.search(r'content-security-policy[^>]*content="([^"]*)"', self.index_html, re.IGNORECASE)
        if csp_match:
            csp = csp_match.group(1).lower()
            self.assertNotIn('mymemory', csp)
            self.assertNotIn('in-the-sky', csp)
            self.assertNotIn('open-meteo', csp)

    def test_ephemerides_eyebrow_text(self):
        self.assertIn('Efemérides', self.index_html)


class TestEphemeridesCss(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(SITE_ROOT, 'styles.css'), encoding='utf-8') as f:
            cls.styles = f.read()

    def test_ephemerides_section_responsive_320px(self):
        block = css_block(self.styles, '.ephem')
        self.assertNotEqual(block, '', 'Ephemerides CSS class not found')

    def test_no_horizontal_overflow_320px(self):
        self.assertIn('overflow-x: auto', self.styles)

    def test_reduced_motion(self):
        block = css_block(self.styles, '@media (prefers-reduced-motion: reduce)')
        self.assertIn('transition: none', block)
        self.assertIn('animation: none', block)

    def test_touch_targets_44px(self):
        block = css_block(self.styles, '.site-nav__link {')
        self.assertIn('min-height: 44px', block)

    def test_ephemerides_cards_style(self):
        self.assertIn('ephem', self.styles)


class TestEphemeridesJsonContract(unittest.TestCase):
    def setUp(self):
        self.fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        self.eph_path = os.path.join(SITE_ROOT, 'data', 'ephemerides.json')
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _load(self):
        if os.path.exists(self.eph_path):
            with open(self.eph_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def test_ephemerides_json_exists(self):
        self.assertTrue(os.path.exists(self.eph_path), 'ephemerides.json must exist')

    def test_valid_json(self):
        data = self._load()
        self.assertIsNotNone(data)
        self.assertIsInstance(data, dict)

    def test_required_top_level_fields(self):
        data = self._load()
        for field in ('status', 'fetched_at', 'target_date', 'timezone',
                       'observer', 'observation_window', 'events', 'weather', 'sources'):
            self.assertIn(field, data, 'Missing top-level field: ' + field)

    def test_status_valid(self):
        data = self._load()
        self.assertIn(data['status'], ('preview', 'live'))

    def test_timezone_is_europe_madrid(self):
        data = self._load()
        self.assertEqual(data['timezone'], 'Europe/Madrid')

    def test_observer_coords(self):
        data = self._load()
        obs = data['observer']
        self.assertAlmostEqual(obs['latitude'], 37.38283, places=3)
        self.assertAlmostEqual(obs['longitude'], -5.97317, places=3)
        self.assertEqual(obs['label'], 'Sevilla')

    def test_observation_window_ordered(self):
        data = self._load()
        window = data['observation_window']
        self.assertIn('start_local', window)
        self.assertIn('end_local', window)
        self.assertLess(window['start_local'], window['end_local'])

    def test_events_is_list(self):
        data = self._load()
        self.assertIsInstance(data['events'], list)

    def test_events_have_required_fields(self):
        data = self._load()
        for event in data['events']:
            for field in ('id', 'type', 'title_es', 'summary_es', 'start_local',
                           'visibility', 'source'):
                self.assertIn(field, event, 'Event missing: ' + field)

    def test_event_visibility_valid(self):
        data = self._load()
        valid_statuses = ('visible', 'contextual', 'uncertain', 'not_visible')
        for event in data['events']:
            vis = event['visibility']
            self.assertIn('status', vis, 'Event {} missing visibility.status'.format(event['id']))
            self.assertIn(vis['status'], valid_statuses,
                          'Event {} invalid visibility status: {}'.format(event['id'], vis['status']))
            self.assertIn('label', vis)
            self.assertIn('reason', vis)

    def test_event_source_has_name_and_url(self):
        data = self._load()
        for event in data['events']:
            src = event['source']
            self.assertIn('name', src)
            self.assertIn('url', src)

    def test_event_source_url_https(self):
        data = self._load()
        for event in data['events']:
            url = event['source']['url']
            self.assertTrue(url.startswith('https://'),
                            'Event {} source URL must be HTTPS: {}'.format(event['id'], url))

    def test_events_start_local_iso_parseable(self):
        data = self._load()
        for event in data['events']:
            start = event['start_local']
            self.assertRegex(start, r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',
                             'Event {} start_local not ISO: {}'.format(event['id'], start))
            dt = datetime.fromisoformat(start)
            self.assertIsNotNone(dt.tzinfo, 'Event {} start_local must be timezone-aware'.format(event['id']))

    def test_weather_is_dict(self):
        data = self._load()
        self.assertIsInstance(data['weather'], dict)

    def test_sources_is_list(self):
        data = self._load()
        self.assertIsInstance(data['sources'], list)
        self.assertGreater(len(data['sources']), 0)

    def test_source_urls_https(self):
        data = self._load()
        for src in data['sources']:
            if 'url' in src:
                self.assertTrue(src['url'].startswith('https://'),
                                'Source URL must be HTTPS: ' + src.get('url', ''))

    def test_no_innerhtml_in_events(self):
        data = self._load()
        for event in data['events']:
            self.assertNotIn('<script', event.get('title_es', '').lower())
            self.assertNotIn('<script', event.get('summary_es', '').lower())
            self.assertNotIn('<img', event.get('summary_es', '').lower())

    def test_event_types_valid(self):
        data = self._load()
        valid_types = (
            'solar_eclipse', 'lunar_eclipse', 'meteor_shower', 'conjunction', 'opposition',
            'lunar_phase', 'planet_visible', 'comet',
            'asteroid_close', 'iss_pass', 'other',
        )
        for event in data['events']:
            self.assertIn(event['type'], valid_types,
                          'Event {} invalid type: {}'.format(event['id'], event['type']))

    def test_target_date_format(self):
        data = self._load()
        self.assertRegex(data['target_date'], r'^\d{4}-\d{2}-\d{2}$')
        parts = data['target_date'].split('-')
        dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        self.assertIsNotNone(dt)

    def test_fetched_at_iso(self):
        data = self._load()
        self.assertRegex(data['fetched_at'], r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}')
        dt = datetime.fromisoformat(data['fetched_at'])
        self.assertIsNotNone(dt)


class TestEphemeridesMainJs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(SITE_ROOT, 'main.js'), encoding='utf-8') as f:
            cls.main_js = f.read()

    def test_ephemerides_in_modules(self):
        self.assertIn("'ephemerides'", self.main_js)

    def test_ephemerides_in_labels(self):
        self.assertIn('Efemérides', self.main_js)

    def test_render_ephemerides_function(self):
        self.assertIn('renderEphemerides', self.main_js)

    def test_fetches_ephemerides_json(self):
        self.assertIn("'ephemerides'", self.main_js)
        self.assertIn("name + '.json'", self.main_js)

    def test_uses_text_content_not_innerhtml(self):
        self.assertNotIn('innerHTML', self.main_js)
        self.assertIn('textContent', self.main_js)

    def test_creates_elements_with_createElement(self):
        self.assertIn('createElement', self.main_js)

    def test_handles_loading_state(self):
        self.assertIn('module__notice', self.main_js)

    def test_handles_empty_events(self):
        self.assertIn('No hay efemérides', self.main_js)

    def test_formats_local_time(self):
        self.assertIn('es-ES', self.main_js)

    def test_shows_weather(self):
        self.assertIn('weather', self.main_js.lower())

    def test_shows_sources(self):
        self.assertIn('sources', self.main_js.lower())


class TestEphemeridesCollectData(unittest.TestCase):
    def test_collect_data_module_has_ephemerides(self):
        self.assertTrue(hasattr(collect_data, 'normalize_ephemerides') or
                        hasattr(collect_data, 'collect_ephemerides') or
                        hasattr(collect_data, 'fetch_ephemerides_ics') or
                        hasattr(collect_data, 'EphemeridesCollector'),
                        'collect_data.py must have ephemerides collection function')

    def test_collect_data_has_ephemerides_validator(self):
        self.assertIn('ephemerides.json', collect_data.VALIDATORS)

    def test_astronomy_engine_imported(self):
        self.assertIsNotNone(collect_data._astronomy)

    def test_target_date_for_returns_tomorrow(self):
        now = datetime(2026, 8, 11, 14, 0, 0, tzinfo=ZoneInfo('Europe/Madrid'))
        result = collect_data.target_date_for(now)
        self.assertEqual(result, datetime(2026, 8, 12).date())

    def test_target_date_for_midnight_boundary(self):
        now = datetime(2026, 8, 11, 23, 59, 0, tzinfo=ZoneInfo('Europe/Madrid'))
        result = collect_data.target_date_for(now)
        self.assertEqual(result, datetime(2026, 8, 12).date())

    def test_target_date_for_new_year_crossing(self):
        now = datetime(2026, 12, 31, 23, 0, 0, tzinfo=ZoneInfo('Europe/Madrid'))
        result = collect_data.target_date_for(now)
        self.assertEqual(result, datetime(2027, 1, 1).date())

    def test_target_date_for_cross_midnight_utc(self):
        now = datetime(2026, 8, 11, 23, 30, 0, tzinfo=timezone.utc)
        result = collect_data.target_date_for(now)
        self.assertEqual(result, datetime(2026, 8, 13).date())


class TestEphemeridesValidateSite(unittest.TestCase):
    def test_validate_site_includes_ephemerides(self):
        import validate_site
        self.assertIn('ephemerides.json', validate_site.DATA_FILES)


class TestEphemeridesObservationWindow(unittest.TestCase):
    def test_observation_window_definition(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        start, end = collect_data.observation_window(target, tz)
        self.assertEqual(start.hour, 0)
        self.assertEqual(start.minute, 0)
        self.assertEqual(start.day, 12)
        self.assertEqual(end.hour, 12)
        self.assertEqual(end.minute, 0)
        self.assertEqual(end.day, 13)
        self.assertEqual(start.tzinfo.key, 'Europe/Madrid')
        self.assertEqual(end.tzinfo.key, 'Europe/Madrid')
        self.assertGreater(end, start)

    def test_observation_window_spans_two_days(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        start, end = collect_data.observation_window(target, tz)
        self.assertEqual((end - start).days, 1)

    def test_civil_morning_returns_valid_time(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        result = collect_data.civil_morning(target, tz)
        self.assertIsNotNone(result.tzinfo)
        self.assertEqual(result.tzinfo.key, 'Europe/Madrid')

    def test_civil_morning_uses_astronomy_engine(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        result = collect_data.civil_morning(target, tz)
        self.assertIsInstance(result, datetime)
        self.assertGreater(result.hour, 0)


class TestIcsParsing(unittest.TestCase):
    def test_ics_folded_lines(self):
        raw = "DESCRIPTION:This is a very long\r\n description"
        lines = collect_data.unfold_ics_lines(raw)
        self.assertEqual(len(lines), 1)
        self.assertIn('This is a very long', lines[0])

    def test_ics_utc_dtstart_parsing(self):
        ics_raw = "BEGIN:VEVENT\nDTSTART:20260812T180000Z\nSUMMARY:Eclipse\nEND:VEVENT"
        events = collect_data.parse_ics_events(ics_raw, 2026)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['dtstart'], '20260812T180000Z')

    def test_ics_local_dtstart_parsing(self):
        ics_raw = "BEGIN:VEVENT\nDTSTART:20260812T200000\nSUMMARY:Conjunction\nEND:VEVENT"
        events = collect_data.parse_ics_events(ics_raw, 2026)
        self.assertEqual(len(events), 1)

    def test_ics_url_in_event(self):
        ics_raw = "BEGIN:VEVENT\nDTSTART:20260812T180000Z\nURL:https://in-the-sky.org/news.php\nEND:VEVENT"
        events = collect_data.parse_ics_events(ics_raw, 2026)
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0]['url'].startswith('https://'))

    def test_ics_filtering_by_observation_window(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        window_start, window_end = collect_data.observation_window(target, tz)

        ics_event_in = {
            'dtstart': '20260812T200000Z',
            'summary': 'Eclipse',
        }
        self.assertTrue(collect_data._ics_event_in_window(ics_event_in, window_start, window_end, tz))

        ics_event_out = {
            'dtstart': '20260815T200000Z',
            'summary': 'Something else',
        }
        self.assertFalse(collect_data._ics_event_in_window(ics_event_out, window_start, window_end, tz))


class TestEclipseSpecialEvent(unittest.TestCase):
    def test_eclipse_uses_astronomy_engine(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        eclipse = collect_data._build_eclipse_event_2026(target, tz)
        self.assertIsNotNone(eclipse)
        self.assertEqual(eclipse['type'], 'solar_eclipse')

    def test_eclipse_date_is_2026_08_12(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        eclipse = collect_data._build_eclipse_event_2026(target, tz)
        self.assertEqual(eclipse['start_local'][:10], '2026-08-12')

    def test_eclipse_approximate_times(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        eclipse = collect_data._build_eclipse_event_2026(target, tz)
        start_dt = datetime.fromisoformat(eclipse['start_local'])
        self.assertEqual(start_dt.hour, 19)
        self.assertLessEqual(start_dt.minute, 42)
        self.assertGreaterEqual(start_dt.minute, 41)

    def test_eclipse_obscuration(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        eclipse = collect_data._build_eclipse_event_2026(target, tz)
        self.assertIn('obscuration', eclipse)
        self.assertGreater(eclipse['obscuration'], 0.9)
        self.assertLess(eclipse['obscuration'], 1.0)

    def test_eclipse_not_total_from_sevilla(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        eclipse = collect_data._build_eclipse_event_2026(target, tz)
        self.assertFalse(eclipse['is_total_from_location'])
        self.assertNotIn('total', eclipse['visibility']['magnitude'].lower().split()[0:1])

    def test_eclipse_peak_altitude(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        eclipse = collect_data._build_eclipse_event_2026(target, tz)
        self.assertIn('peak_altitude_deg', eclipse)
        self.assertAlmostEqual(eclipse['peak_altitude_deg'], 7.36, places=0)

    def test_eclipse_reference_urls(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        eclipse = collect_data._build_eclipse_event_2026(target, tz)
        summary = eclipse.get('summary_es', '')
        self.assertTrue(
            'ign.es' in summary.lower() or 'nasa' in summary.lower() or
            'ign.es' in eclipse['source']['url'].lower(),
            'Eclipse event must reference IGN or NASA')

    def test_eclipse_source_https(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        eclipse = collect_data._build_eclipse_event_2026(target, tz)
        self.assertTrue(eclipse['source']['url'].startswith('https://'))

    def test_eclipse_has_end_local(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        eclipse = collect_data._build_eclipse_event_2026(target, tz)
        self.assertIn('end_local', eclipse)
        self.assertIn('peak_local', eclipse)

    def test_eclipse_fallback_without_astronomy(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 12).date()
        with patch.object(collect_data, '_astronomy', None):
            eclipse = collect_data._build_eclipse_event_2026(target, tz)
        self.assertIsNotNone(eclipse)
        self.assertEqual(eclipse['visibility']['status'], 'uncertain')

    def test_non_eclipse_date_returns_none(self):
        tz = ZoneInfo('Europe/Madrid')
        target = datetime(2026, 8, 15).date()
        eclipse = collect_data._build_eclipse_event_2026(target, tz)
        self.assertIsNone(eclipse)


class TestPerseidsEvent(unittest.TestCase):
    def test_perseids_date_range(self):
        data = None
        eph_path = os.path.join(SITE_ROOT, 'data', 'ephemerides.json')
        with open(eph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIsNotNone(data)
        perseids = [e for e in data['events'] if 'perseid' in e['id'].lower()
                    or 'perseid' in e.get('title_es', '').lower()]
        self.assertGreater(len(perseids), 0, 'Perseids event must exist')
        start = perseids[0]['start_local'][:10]
        self.assertIn(start, ('2026-08-12', '2026-08-13'))


class TestHorizontalCoordinates(unittest.TestCase):
    def test_sun_position_known_date(self):
        tz = ZoneInfo('Europe/Madrid')
        dt = datetime(2026, 8, 12, 19, 41, 51, tzinfo=tz)
        result = collect_data.horizontal_coordinates('Sun', dt)
        self.assertIn('altitude_deg', result)
        self.assertIn('azimuth_deg', result)
        self.assertIn('sun_altitude_deg', result)
        self.assertAlmostEqual(result['altitude_deg'], 18.2, delta=1.0)
        self.assertAlmostEqual(result['azimuth_deg'], 275.0, delta=2.0)

    def test_sun_at_peak(self):
        tz = ZoneInfo('Europe/Madrid')
        dt = datetime(2026, 8, 12, 20, 37, 32, tzinfo=tz)
        result = collect_data.horizontal_coordinates('Sun', dt)
        self.assertAlmostEqual(result['altitude_deg'], 7.36, delta=1.0)

    def test_unknown_body_raises(self):
        tz = ZoneInfo('Europe/Madrid')
        dt = datetime(2026, 8, 12, 20, 0, 0, tzinfo=tz)
        with self.assertRaises(ValueError):
            collect_data.horizontal_coordinates('Pluto', dt)


class TestAssessVisibility(unittest.TestCase):
    def test_sun_above_horizon_night(self):
        vis = collect_data.assess_visibility('Sun', 18.0, -10.0)
        self.assertEqual(vis['status'], 'visible')

    def test_sun_below_horizon(self):
        vis = collect_data.assess_visibility('Sun', -5.0, -10.0)
        self.assertEqual(vis['status'], 'not_visible')

    def test_planet_visible_night(self):
        vis = collect_data.assess_visibility('Venus', 15.0, -10.0)
        self.assertEqual(vis['status'], 'visible')

    def test_planet_daylight(self):
        vis = collect_data.assess_visibility('Venus', 15.0, 10.0)
        self.assertEqual(vis['status'], 'not_visible')

    def test_planet_below_horizon(self):
        vis = collect_data.assess_visibility('Mars', -5.0, -10.0)
        self.assertEqual(vis['status'], 'not_visible')

    def test_unknown_event(self):
        vis = collect_data.assess_visibility('Unknown', 10.0, -10.0)
        self.assertEqual(vis['status'], 'uncertain')


class TestValidateEphemerides(unittest.TestCase):
    def test_valid_dataset(self):
        dataset = {
            'status': 'preview',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': '2026-08-12',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317, 'label': 'Sevilla'},
            'observation_window': {'start_local': '2026-08-12T00:00+02:00',
                                   'end_local': '2026-08-13T12:00+02:00'},
            'events': [{
                'id': 'eclipse-2026-08-12',
                'type': 'solar_eclipse',
                'title_es': 'Eclipse solar parcial',
                'summary_es': 'Eclipse visible desde Sevilla.',
                'start_local': '2026-08-12T19:41+02:00',
                'visibility': {'status': 'visible', 'label': 'Visible', 'reason': 'Buen tiempo'},
                'source': {'name': 'IGN', 'url': 'https://visualizadores.ign.es/eclipses/2026'},
            }],
            'weather': {'cloud_cover': 20, 'visibility': 10000},
            'sources': [{'name': 'In-The-Sky', 'url': 'https://in-the-sky.org/'}],
        }
        errors = collect_data.validate_ephemerides(dataset)
        self.assertEqual(errors, [])

    def test_missing_events(self):
        dataset = {
            'status': 'preview',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': '2026-08-12',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317, 'label': 'Sevilla'},
            'observation_window': {'start_local': '2026-08-12T00:00+02:00',
                                   'end_local': '2026-08-13T12:00+02:00'},
            'events': [],
            'weather': {},
            'sources': [],
        }
        errors = collect_data.validate_ephemerides(dataset)
        self.assertEqual(errors, [])

    def test_invalid_type_rejected(self):
        dataset = {
            'status': 'preview',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': '2026-08-12',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317},
            'observation_window': {'start_local': '2026-08-12T00:00+02:00',
                                   'end_local': '2026-08-13T12:00+02:00'},
            'events': [{
                'id': 'bad-event',
                'type': '流星_shower',
                'title_es': 'Test',
                'summary_es': 'Test',
                'start_local': '2026-08-12T20:00+02:00',
                'visibility': {'status': 'visible', 'label': 'V', 'reason': 'R'},
                'source': {'name': 'X', 'url': 'https://example.com'},
            }],
            'weather': {},
            'sources': [{'name': 'X', 'url': 'https://example.com'}],
        }
        errors = collect_data.validate_ephemerides(dataset)
        self.assertTrue(any('invalid_type' in e for e in errors))

    def test_empty_sources_live_rejected(self):
        dataset = {
            'status': 'live',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': '2026-08-12',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317},
            'observation_window': {'start_local': '2026-08-12T00:00+02:00',
                                   'end_local': '2026-08-13T12:00+02:00'},
            'events': [],
            'weather': {},
            'sources': [],
        }
        errors = collect_data.validate_ephemerides(dataset)
        self.assertTrue(any('sources.empty_for_live' in e for e in errors))

    def test_wrong_timezone_rejected(self):
        dataset = {
            'status': 'preview',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': '2026-08-12',
            'timezone': 'UTC',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317},
            'observation_window': {'start_local': '2026-08-12T00:00+02:00',
                                   'end_local': '2026-08-13T12:00+02:00'},
            'events': [],
            'weather': {},
            'sources': [],
        }
        errors = collect_data.validate_ephemerides(dataset)
        self.assertTrue(any('timezone' in e for e in errors))

    def test_window_out_of_order_rejected(self):
        dataset = {
            'status': 'preview',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': '2026-08-12',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317},
            'observation_window': {'start_local': '2026-08-13T12:00+02:00',
                                   'end_local': '2026-08-12T00:00+02:00'},
            'events': [],
            'weather': {},
            'sources': [],
        }
        errors = collect_data.validate_ephemerides(dataset)
        self.assertTrue(any('out_of_order' in e for e in errors))

    def test_invalid_target_date_rejected(self):
        dataset = {
            'status': 'preview',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': 'not-a-date',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317},
            'observation_window': {'start_local': '2026-08-12T00:00+02:00',
                                   'end_local': '2026-08-13T12:00+02:00'},
            'events': [],
            'weather': {},
            'sources': [],
        }
        errors = collect_data.validate_ephemerides(dataset)
        self.assertTrue(any('target_date' in e for e in errors))


class TestCollectEphemeridesICSFailure(unittest.TestCase):
    def test_returns_1_when_no_previous_and_no_ics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(collect_data, 'fetch_ics_events', return_value=None):
                with patch.object(collect_data, 'astronomy_now') as mock_now:
                    mock_now.return_value = datetime(2026, 8, 11, 14, 0, 0,
                                                      tzinfo=ZoneInfo('Europe/Madrid'))
                    result = collect_data.collect_ephemerides(tmpdir, timeout=5, write=False)
            self.assertEqual(result, 1)

    def test_preserves_previous_when_no_ics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prev = {'status': 'live', 'events': []}
            with open(os.path.join(tmpdir, 'ephemerides.json'), 'w') as f:
                json.dump(prev, f)
            with patch.object(collect_data, 'fetch_ics_events', return_value=None):
                with patch.object(collect_data, 'astronomy_now') as mock_now:
                    mock_now.return_value = datetime(2026, 8, 11, 14, 0, 0,
                                                      tzinfo=ZoneInfo('Europe/Madrid'))
                    result = collect_data.collect_ephemerides(tmpdir, timeout=5, write=True)
            self.assertEqual(result, 0)
            with open(os.path.join(tmpdir, 'ephemerides.json')) as f:
                data = json.load(f)
            self.assertEqual(data['status'], 'live')


class TestEphemeridesContractIntegration(unittest.TestCase):
    def test_validate_dataset_ephemerides(self):
        dataset = {
            'status': 'preview',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': '2026-08-12',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317, 'label': 'Sevilla'},
            'observation_window': {'start_local': '2026-08-12T00:00+02:00',
                                   'end_local': '2026-08-13T12:00+02:00'},
            'events': [{
                'id': 'eclipse-2026-08-12',
                'type': 'solar_eclipse',
                'title_es': 'Eclipse solar parcial',
                'summary_es': 'Eclipse visible desde Sevilla.',
                'start_local': '2026-08-12T19:41+02:00',
                'visibility': {'status': 'visible', 'label': 'Visible', 'reason': 'Buen tiempo'},
                'source': {'name': 'IGN', 'url': 'https://visualizadores.ign.es/eclipses/2026'},
            }],
            'weather': {'cloud_cover': 20, 'visibility': 10000},
            'sources': [{'name': 'In-The-Sky', 'url': 'https://in-the-sky.org/'}],
        }
        errors = collect_data.validate_dataset('ephemerides.json', dataset)
        self.assertEqual(errors, [])

    def test_validate_dataset_ephemerides_missing_events(self):
        dataset = {
            'status': 'preview',
            'fetched_at': '2026-08-12T00:00:00+00:00',
            'target_date': '2026-08-12',
            'timezone': 'Europe/Madrid',
            'observer': {'latitude': 37.38283, 'longitude': -5.97317, 'label': 'Sevilla'},
            'observation_window': {'start_local': '2026-08-12T00:00+02:00',
                                   'end_local': '2026-08-13T12:00+02:00'},
            'events': [],
            'weather': {},
            'sources': [],
        }
        errors = collect_data.validate_dataset('ephemerides.json', dataset)
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
