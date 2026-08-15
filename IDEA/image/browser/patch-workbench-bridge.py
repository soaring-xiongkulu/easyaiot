#!/usr/bin/env python3
from pathlib import Path
import re
import sys

wb = Path('/usr/lib/code-server/lib/vscode/out/vs/code/browser/workbench/workbench.html')
bridge_path = Path('/usr/lib/code-server/src/browser/media/easyaiot-ide-bridge.js')
bridge = bridge_path.read_text(encoding='utf-8')
if '__easyaiotIdeBridge' not in bridge and '__easyaiotHooked' not in bridge:
    print('bridge file missing expected markers', file=sys.stderr)
    sys.exit(1)
html = wb.read_text(encoding='utf-8')
html = re.sub(
    r'\s*<script src="\{\{BASE\}\}/_static/src/browser/media/easyaiot-ide-bridge\.js"></script>\s*',
    '\n',
    html,
)
marker = '<!-- easyaiot-ide-bridge -->'
while marker in html:
    start = html.find(marker)
    end = html.find('</script>', start)
    if end < 0:
        break
    end = html.find('\n', end)
    end = len(html) if end < 0 else end + 1
    html = html[:start] + html[end:]

idx = html.rfind('</html>')
if idx < 0:
    print('no html end', file=sys.stderr)
    sys.exit(1)
safe = bridge.replace('</script>', '<\\/script>')
snippet = (
    '\n\t<!-- easyaiot-ide-bridge -->\n\t<script>\n'
    + safe
    + '\n\t</script>\n</html>\n'
)
html = html[:idx] + snippet
wb.write_text(html, encoding='utf-8')
text = wb.read_text(encoding='utf-8')
print('size', len(text))
print('portal_guard', text.count('location.replace'))
print('ext_src', text.count('_static/src/browser/media/easyaiot-ide-bridge.js'))
