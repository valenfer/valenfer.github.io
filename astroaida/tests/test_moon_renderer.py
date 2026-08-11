import json
import os
import unittest

SITE_ROOT = os.path.join(os.path.dirname(__file__), '..')


def css_block(css, selector):
    start = css.find(selector)
    if start == -1:
        return ''
    brace = css.find('{', start)
    end = css.find('}', brace)
    if brace == -1 or end == -1:
        return ''
    return css[brace + 1:end]


class TestMoonRendererIntegration(unittest.TestCase):
    """Static regression: the moon module must render a local canvas via
    moon-renderer.js instead of embedding the remote AstronomyAPI PNG, keep
    the original JSON fields untouched and expose a Spanish accessible label."""

    def setUp(self):
        with open(os.path.join(SITE_ROOT, 'moon-renderer.js'), encoding='utf-8') as f:
            self.renderer_js = f.read()
        with open(os.path.join(SITE_ROOT, 'main.js'), encoding='utf-8') as f:
            self.main_js = f.read()
        with open(os.path.join(SITE_ROOT, 'index.html'), encoding='utf-8') as f:
            self.index_html = f.read()
        with open(os.path.join(SITE_ROOT, 'styles.css'), encoding='utf-8') as f:
            self.styles = f.read()
        with open(os.path.join(SITE_ROOT, 'data', 'moon.json'), encoding='utf-8') as f:
            self.moon_json = json.load(f)

    def test_renderer_is_umd_for_browser_and_node(self):
        self.assertIn('module.exports = factory()', self.renderer_js)
        self.assertIn('root.MoonRenderer = factory()', self.renderer_js)

    def test_renderer_exports_pure_geometry_and_render(self):
        for export_name in ('clampIllumination', 'translatePhase', 'phaseParams',
                            'lunarBrightnessAt', 'renderMoon'):
            self.assertIn(export_name + ':', self.renderer_js)

    def test_main_js_uses_canvas_renderer(self):
        self.assertIn('window.MoonRenderer', self.main_js)
        self.assertIn('window.MoonRenderer.renderMoon', self.main_js)
        self.assertIn("el('canvas', 'moon__canvas')", self.main_js)

    def test_main_js_no_longer_embeds_remote_moon_image(self):
        self.assertNotIn('moduleImage(data.image_url, \'Fase lunar\')', self.main_js)

    def test_canvas_has_role_img_and_spanish_aria_label(self):
        self.assertIn("canvas.setAttribute('role', 'img');", self.main_js)
        self.assertIn("canvas.setAttribute('aria-label', 'Fase lunar: '", self.main_js)

    def test_interface_uses_spanish_phase_translation(self):
        self.assertIn('window.MoonRenderer.translatePhase(data.phase)', self.main_js)

    def test_renderer_loaded_before_main(self):
        moon_pos = self.index_html.find('moon-renderer.js')
        main_pos = self.index_html.find('main.js')
        self.assertNotEqual(moon_pos, -1, 'moon-renderer.js must be referenced')
        self.assertNotEqual(main_pos, -1, 'main.js must be referenced')
        self.assertLess(moon_pos, main_pos)

    def test_styles_style_the_canvas(self):
        block = css_block(self.styles, '.moon__figure canvas {')
        self.assertIn('width', block)
        self.assertIn('aspect-ratio', block)

    def test_moon_json_keeps_original_fields_for_compatibility(self):
        phase = self.moon_json['phase']
        self.assertIsInstance(phase, str)
        self.assertTrue(phase.strip(), 'phase must be a non-empty string')
        illumination = self.moon_json['illumination']
        self.assertIsInstance(illumination, (int, float))
        self.assertGreaterEqual(illumination, 0.0)
        self.assertLessEqual(illumination, 1.0)
        self.assertIn('image_url', self.moon_json)


if __name__ == '__main__':
    unittest.main()
