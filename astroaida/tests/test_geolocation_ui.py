import os
import unittest

SITE_ROOT = os.path.join(os.path.dirname(__file__), '..')


class TestGeolocationUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(SITE_ROOT, 'index.html'), encoding='utf-8') as f:
            cls.index_html = f.read()
        with open(os.path.join(SITE_ROOT, 'main.js'), encoding='utf-8') as f:
            cls.main_js = f.read()
        with open(os.path.join(SITE_ROOT, 'styles.css'), encoding='utf-8') as f:
            cls.styles = f.read()

    def test_location_section_exists(self):
        self.assertIn('id="location"', self.index_html)
        self.assertIn('data-module="location"', self.index_html)
        self.assertIn('Usar mi GPS', self.index_html)

    def test_location_form_has_manual_coordinates(self):
        self.assertIn('name="latitude"', self.index_html)
        self.assertIn('name="longitude"', self.index_html)
        self.assertIn('name="elevation"', self.index_html)
        self.assertIn('id="observer-latitude"', self.index_html)
        self.assertIn('required aria-describedby="location-status"', self.index_html)

    def test_geolocation_api_is_used_only_after_button_click(self):
        gps_index = self.main_js.index('navigator.geolocation.getCurrentPosition')
        click_index = self.main_js.index("gpsButton.addEventListener('click'")
        init_index = self.main_js.index('function init()')
        self.assertGreater(gps_index, click_index)
        self.assertLess(gps_index, init_index)
        self.assertIn("data-action=\"gps\"", self.index_html)
        self.assertIn('enableHighAccuracy: true', self.main_js)

    def test_location_is_local_only(self):
        self.assertIn('window.localStorage.setItem', self.main_js)
        self.assertIn('window.localStorage.removeItem', self.main_js)
        self.assertIn('no se envía a ningún servidor', self.index_html)
        location_block = self.main_js[self.main_js.index('function initLocationControls'):self.main_js.index('function isSafeHttpUrl')]
        self.assertNotIn('fetch(', location_block)
        self.assertNotIn('sendBeacon', location_block)

    def test_location_controls_are_mobile_safe(self):
        self.assertIn('.location-panel__button', self.styles)
        self.assertIn('min-height: 44px', self.styles)
        self.assertIn('@media (max-width: 520px)', self.styles)

    def test_empty_coordinates_are_rejected(self):
        self.assertIn("if (text === '') { return null; }", self.main_js)
        self.assertIn("aria-invalid", self.main_js)

    def test_observer_label_exists_for_header_update(self):
        self.assertIn('data-role="observer-label"', self.index_html)


if __name__ == '__main__':
    unittest.main()
