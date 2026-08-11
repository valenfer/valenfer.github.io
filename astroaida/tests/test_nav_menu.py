import html.parser
import os
import unittest

SITE_ROOT = os.path.join(os.path.dirname(__file__), '..')

EXPECTED_LINKS = [
    ('#apod', 'Astronomía del día'),
    ('#sky-today', 'Cielo hoy'),
    ('#moon', 'Luna'),
    ('#star-chart', 'Carta celeste'),
    ('#near-earth', 'Asteroides'),
    ('#ephemerides', 'Efemérides'),
]

EXPECTED_SECTIONS = ['apod', 'sky-today', 'moon', 'star-chart', 'near-earth', 'ephemerides']


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


class NavParser(html.parser.HTMLParser):
    """Extracts the header section nav contract from index.html."""

    def __init__(self):
        super().__init__()
        self.nav_labels = []
        self.nav_links = []
        self.doc_ids = []
        self.section_ids = []
        self.buttons = []
        self._in_nav = 0
        self._in_link = False
        self._link_href = None
        self._link_text = []

    def handle_starttag(self, tag, attrs):
        values = {key: value or '' for key, value in attrs}
        id_value = values.get('id')
        if id_value:
            self.doc_ids.append(id_value)
        if tag == 'nav':
            label = values.get('aria-label')
            if label:
                self.nav_labels.append(label)
            self._in_nav += 1
        elif tag == 'section':
            section_id = values.get('id')
            if section_id:
                self.section_ids.append(section_id)
        elif tag == 'a' and self._in_nav:
            self._in_link = True
            self._link_href = values.get('href')
            self._link_text = []
        elif tag == 'button':
            self.buttons.append(values.get('class', ''))

    def handle_endtag(self, tag):
        if tag == 'nav':
            self._in_nav -= 1
        elif tag == 'a' and self._in_link:
            self._in_link = False
            if self._link_href:
                self.nav_links.append((self._link_href, ''.join(self._link_text).strip()))

    def handle_data(self, data):
        if self._in_link:
            self._link_text.append(data)


class TestNavMenuContract(unittest.TestCase):
    """Static contract: the header nav jumps to every section without JS and
    without ever widening the page. It is sticky, has visible focus, touch
    targets of at least 44px and only animates scroll when the user allows."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(SITE_ROOT, 'index.html'), encoding='utf-8') as f:
            cls.index_html = f.read()
        with open(os.path.join(SITE_ROOT, 'styles.css'), encoding='utf-8') as f:
            cls.styles = f.read()
        with open(os.path.join(SITE_ROOT, 'main.js'), encoding='utf-8') as f:
            cls.main_js = f.read()
        cls.parser = NavParser()
        cls.parser.feed(cls.index_html)

    def test_nav_present_with_spanish_aria_label(self):
        self.assertEqual(self.parser.nav_labels, ['Secciones de la página'])

    def test_nav_links_match_expected_sections(self):
        self.assertEqual(self.parser.nav_links, EXPECTED_LINKS)

    def test_nav_hrefs_target_exact_unique_ids(self):
        for href, _ in EXPECTED_LINKS:
            target = href[1:]
            self.assertEqual(
                self.parser.doc_ids.count(target), 1,
                '{} must be assigned exactly once, got {}'.format(
                    target, self.parser.doc_ids.count(target)))

    def test_sections_have_stable_ids(self):
        self.assertEqual(self.parser.section_ids, EXPECTED_SECTIONS)

    def test_no_hamburger_and_no_js_build(self):
        self.assertEqual(self.parser.buttons, [])
        self.assertNotIn('site-nav', self.main_js)
        self.assertNotIn('hamburger', self.main_js.lower())

    def test_nav_is_sticky_and_contained(self):
        block = css_block(self.styles, '.site-nav {')
        self.assertIn('position: sticky', block)
        self.assertIn('top: 0', block)
        self.assertIn('overflow-x: auto', block)
        self.assertIn('max-width: 100%', block)

    def test_nav_list_wraps_without_page_overflow(self):
        block = css_block(self.styles, '.site-nav__list {')
        self.assertIn('flex-wrap: wrap', block)
        self.assertIn('max-width', block)

    def test_nav_links_meet_44px_touch_target(self):
        block = css_block(self.styles, '.site-nav__link {')
        self.assertIn('min-height: 44px', block)

    def test_nav_focus_visible(self):
        block = css_block(self.styles, '.site-nav__link:focus-visible {')
        self.assertIn('outline', block)

    def test_sections_have_scroll_margin_top(self):
        block = css_block(self.styles, 'section[id]')
        self.assertIn('scroll-margin-top', block)

    def test_smooth_scroll_only_when_motion_ok(self):
        ok_block = css_block(self.styles, '@media (prefers-reduced-motion: no-preference)')
        reduce_block = css_block(self.styles, '@media (prefers-reduced-motion: reduce)')
        self.assertIn('scroll-behavior: smooth', ok_block)
        self.assertNotIn('scroll-behavior', reduce_block)


if __name__ == '__main__':
    unittest.main()
