"""Check scaffold consistency; does not validate flight physics or paper claims."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
for name in ['AGENTS.md', 'README.md', 'docs/guides/PROTOCOL.md', 'docs/paper/Research-Paper.tex']:
    if not (root / name).is_file():
        raise SystemExit(f'Missing {name}')
cfg = json.loads((root / 'configs/pilot.json').read_text())
if cfg['status'] != 'proposal' or cfg['backend'] != 'unselected':
    raise SystemExit('Update scaffold check when backend selection is documented')
print('Scaffold checks passed. Physics, results and manuscript remain unvalidated.')
