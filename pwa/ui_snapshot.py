"""Build a non-interactive copy of the app's original HTML and CSS."""

import html
import json
import re
from html.parser import HTMLParser


SNAPSHOT_BEGIN = '<!-- Velvitty UI snapshot -->'
SNAPSHOT_END = '<!-- /Velvitty UI snapshot -->'
SNAPSHOT_BLOCK = re.compile(re.escape(SNAPSHOT_BEGIN) + r'[\s\S]*?' + re.escape(SNAPSHOT_END))


def theme_profile(source):
    source = re.sub(r'<!-- Velvitty launch screen -->[\s\S]*?<!-- /Velvitty launch screen -->', '', source)
    scripts = '\n'.join(re.findall(r'<script\b[^>]*>([\s\S]*?)</script\s*>', source, re.I))
    profile = None
    if 'prefs.theme' in scripts:
        current = re.search(r"\bPREF_KEY\s*=\s*['\"]([^'\"]+)['\"]", scripts)
        legacy = re.search(r"\bOLD_PREF_KEY\s*=\s*['\"]([^'\"]+)['\"]", scripts)
        if current:
            profile = {'keys': [current[1]] + ([legacy[1]] if legacy else []), 'field': 'theme'}
    if not profile:
        key = re.search(r"localStorage\s*\.\s*getItem\(\s*['\"]([^'\"]*theme[^'\"]*)['\"]", scripts, re.I)
        if key and ('dataset.theme' in scripts or 'data-theme' in scripts):
            profile = {'keys': [key[1]]}
    if profile:
        default = re.search(r'(?<![-\w])color-scheme\s*:\s*(light|dark)\b', source)
        profile['default'] = default[1] if default else 'light'
    return profile


class StaticUI(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []
        self.skipped = 0

    def handle_starttag(self, tag, attrs):
        containers = {'script', 'iframe', 'object'}
        if tag in containers:
            self.skipped += 1
            return
        if self.skipped or tag in {'base', 'embed'}:
            return
        values = dict(attrs)
        if tag == 'meta' and values.get('http-equiv'):
            return
        if tag == 'link' and values.get('rel', '').lower() not in {'stylesheet'}:
            return
        safe = []
        for name, value in attrs:
            if name.lower().startswith('on'):
                continue
            safe.append(name if value is None else name + '="' + html.escape(value, quote=True) + '"')
        if tag == 'body' and 'inert' not in values:
            safe.append('inert')
        self.parts.append('<' + tag + (' ' + ' '.join(safe) if safe else '') + '>')

    def handle_endtag(self, tag):
        if tag in {'script', 'iframe', 'object'}:
            self.skipped = max(0, self.skipped - 1)
            return
        if not self.skipped and tag not in {'base', 'embed'}:
            self.parts.append('</' + tag + '>')

    def handle_startendtag(self, tag, attrs):
        if tag in {'script', 'iframe', 'object'}:
            return
        previous = len(self.parts)
        self.handle_starttag(tag, attrs)
        if len(self.parts) > previous:
            self.parts[-1] = self.parts[-1][:-1] + '/>'

    def handle_data(self, data):
        if not self.skipped:
            self.parts.append(data)

    def handle_entityref(self, name):
        self.handle_data('&' + name + ';')

    def handle_charref(self, name):
        self.handle_data('&#' + name + ';')

    def handle_decl(self, declaration):
        if not self.skipped:
            self.parts.append('<!' + declaration + '>')


def make_snapshot(source):
    profile = theme_profile(source)
    source = re.sub(r'<!-- Velvitty launch screen -->[\s\S]*?<!-- /Velvitty launch screen -->', '', source)
    source = SNAPSHOT_BLOCK.sub('', source)
    # Background text uses the app's font fallback instead of duplicating embedded font files.
    source = re.sub(r'@font-face\s*\{[^}]*\}', '', source, flags=re.I)
    parser = StaticUI()
    parser.feed(source)
    parser.close()
    result = ''.join(parser.parts)
    theme = '<!-- velvitty-ui-theme ' + json.dumps(profile, separators=(',', ':')) + ' -->' if profile else ''
    policy = '''<base href="./"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'none'; connect-src 'none'; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' data: https:; frame-src 'none'; object-src 'none'; form-action 'none'; base-uri 'self'"><style>html{pointer-events:none!important}*{animation-play-state:paused!important;caret-color:transparent!important}</style>'''
    return re.sub(r'<head\b[^>]*>', lambda m: m[0] + theme + policy, result, count=1, flags=re.I)


def snapshot_block(snapshot):
    return SNAPSHOT_BEGIN + '\n<template id="velvitty-ui-fallback">' + html.escape(snapshot) + '</template>\n' + SNAPSHOT_END + '\n'


def replace_snapshot_block(document, snapshot):
    return SNAPSHOT_BLOCK.sub(lambda _: snapshot_block(snapshot).rstrip('\n'), document, count=1)
