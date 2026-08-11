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


class TestSkyTableMobileOverflow(unittest.TestCase):
    """Static regression: on narrow viewports the sky table used to widen the
    document (scrollWidth > clientWidth). It must live in a scrollable region
    so the page never overflows horizontally."""

    def setUp(self):
        with open(os.path.join(SITE_ROOT, 'main.js'), encoding='utf-8') as f:
            self.main_js = f.read()
        with open(os.path.join(SITE_ROOT, 'styles.css'), encoding='utf-8') as f:
            self.styles = f.read()

    def test_main_js_wraps_sky_table_in_region(self):
        self.assertIn("var region = el('div', 'sky-table-region');", self.main_js)
        self.assertIn('region.appendChild(table);', self.main_js)

    def test_region_has_role_and_aria_label(self):
        self.assertIn("region.setAttribute('role', 'region');", self.main_js)
        self.assertIn("region.setAttribute('aria-label'", self.main_js)

    def test_region_is_keyboard_focusable(self):
        self.assertIn("region.setAttribute('tabindex', '0');", self.main_js)

    def test_region_has_visible_spanish_hint(self):
        self.assertIn('Desliza en horizontal', self.main_js)

    def test_region_contains_table_hint_in_spanish(self):
        self.assertIn('Desliza en horizontal para ver la tabla completa.', self.main_js)

    def test_styles_scope_overflow_to_region(self):
        block = css_block(self.styles, '.sky-table-region {')
        self.assertIn('overflow-x: auto', block)
        self.assertIn('max-width: 100%', block)

    def test_styles_give_table_a_min_width(self):
        block = css_block(self.styles, '.sky-table {')
        self.assertIn('min-width', block)

    def test_styles_hint_is_muted_and_small(self):
        block = css_block(self.styles, '.sky-table-region__hint {')
        self.assertIn('font-size', block)
        self.assertIn('text-muted', block)


if __name__ == '__main__':
    unittest.main()
