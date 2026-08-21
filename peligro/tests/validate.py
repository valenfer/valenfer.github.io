from pathlib import Path
from html.parser import HTMLParser
root=Path(__file__).resolve().parents[1]
for name in ['index.html','styles.css','script.js','README.md']:
    p=root/name
    assert p.exists() and p.stat().st_size>500, f'{name} missing or too small'
html=(root/'index.html').read_text(encoding='utf-8')
for text in ['Huella digital','Anti-manipulación','Debate histórico','Simulador de crisis','Phishing ético','Noticias sesgadas','Vigilancia cotidiana','Escape IA']:
    assert text in html, text
assert 'file://' not in html
assert 'href="#"' not in html
class Parser(HTMLParser):
    def error(self, message): raise AssertionError(message)
Parser().feed(html)
print('VALIDATION_OK: estructura, contenido y referencias básicas correctas')
