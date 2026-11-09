"""Refresh the static PWA background after editing illustracy.html (stdlib only)."""
from pathlib import Path
import hashlib
import html
import json
import re
from ui_snapshot import make_snapshot, replace_snapshot_block, theme_profile

ROOT = Path(__file__).resolve().parent.parent
source = (ROOT / 'illustracy.html').read_text(encoding='utf-8')
snapshot = make_snapshot(source)
snapshot = snapshot.replace('</head>', '<style>header .tseg .opt[aria-checked="true"]{background:var(--sel)!important;box-shadow:inset 0 -2px 0 var(--accent)}</style></head>', 1)
profile = theme_profile(source)
if not profile:
    raise SystemExit('Check the application theme storage before refreshing the PWA.')
profile_json = json.dumps(profile, separators=(',', ':'))
entry = replace_snapshot_block((ROOT / 'index.html').read_text(encoding='utf-8'), snapshot)
entry = re.sub(r'readUITheme\(\{[^\n]*?\}\)\.theme', lambda _: 'readUITheme(' + profile_json + ').theme', entry)
offline = (ROOT / 'offline.html').read_text(encoding='utf-8')
offline = re.sub(r'srcdoc="[^"]*"', lambda _: 'srcdoc="' + html.escape(snapshot, quote=True) + '"', offline, count=1)
offline = re.sub(r'readUITheme\(\{[^\n]*?\}\)\.theme', lambda _: 'readUITheme(' + profile_json + ').theme', offline)
for name, value in {'index.html': entry, 'offline.html': offline, 'pwa-ui.html': snapshot}.items():
    (ROOT / name).write_text(value, encoding='utf-8')
worker = (ROOT / 'sw.js').read_text(encoding='utf-8')
signature = re.sub(r'const VERSION = "[^"]*";', 'const VERSION = "";', worker, count=1)
digest = hashlib.sha256(signature.encode())
for name in ('illustracy.html', 'index.html', 'offline.html', 'pwa-ui.html', 'pwa.js', 'manifest.webmanifest', 'pwa-icon-192.png', 'pwa-icon-512.png', 'pwa-icon-maskable.png', 'apple-touch-icon.png'):
    digest.update(name.encode() + b'\0' + (ROOT / name).read_bytes())
version = digest.hexdigest()[:16]
worker = re.sub(r'const VERSION = "[^"]*";', f'const VERSION = "{version}";', worker, count=1)
(ROOT / 'sw.js').write_text(worker, encoding='utf-8')
print(f'Updated Illustracy PWA background and cache version {version}.')
