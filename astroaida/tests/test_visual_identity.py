import os
import unittest

SITE_ROOT = os.path.join(os.path.dirname(__file__), '..')


class TestAstroAidaVisualIdentity(unittest.TestCase):
    """Static regression tests for the AstroAIDA astronomical visual identity."""

    def setUp(self):
        with open(os.path.join(SITE_ROOT, 'index.html'), encoding='utf-8') as f:
            self.html = f.read()
        with open(os.path.join(SITE_ROOT, 'styles.css'), encoding='utf-8') as f:
            self.css = f.read()

    def test_header_uses_observatory_editorial_copy(self):
        self.assertIn('Observatorio AstroAIDA', self.html)
        self.assertIn('Bitácora celeste', self.html)
        self.assertIn('Observatorio nocturno de Sevilla', self.html)

    def test_css_contains_deep_space_design_tokens(self):
        self.assertIn('--deep-space', self.css)
        self.assertIn('--observatory', self.css)
        self.assertIn('--lunar', self.css)
        self.assertIn('--solar', self.css)

    def test_css_builds_starfield_and_celestial_grid(self):
        self.assertIn('body::before', self.css)
        self.assertIn('radial-gradient(circle', self.css)
        self.assertIn('site-header::before', self.css)
        self.assertIn('slow-orbit', self.css)

    def test_navigation_keeps_wrapping_without_page_overflow(self):
        self.assertIn('overflow-x: auto', self.css)
        self.assertIn('flex-wrap: wrap', self.css)
        self.assertIn('max-width: 100%', self.css)
        self.assertIn('min-height: 44px', self.css)


if __name__ == '__main__':
    unittest.main()
