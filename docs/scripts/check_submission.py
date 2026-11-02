"""Local submission indicators; not a complete policy or readiness certification."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path)
    args = parser.parse_args()
    config = json.loads((ROOT / 'configs/submission.json').read_text())
    paper = ROOT / 'docs/paper/Research-Paper.tex'
    text = '\n'.join(line.split('%', 1)[0] for line in paper.read_text().splitlines())
    if r'\documentclass[letterpaper,10pt,conference]{ieeeconf}' not in text:
        raise SystemExit('Expected recorded PaperCept template options')
    if r'\overrideIEEEmargins' not in text:
        raise SystemExit('Expected template margin command')
    for marker in [r'\author{', r'\thanks{', 'Thavarshan', 'jerome', 'github.com/Thavarshan']:
        if marker.lower() in text.lower():
            raise SystemExit(f'Potential anonymous-review identifier: {marker}')
    for asset in ['ieeeconf.cls', 'IEEEtran.bst']:
        data = (paper.parent / asset).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest not in (paper.parent / 'TEMPLATE_PROVENANCE.md').read_text():
            raise SystemExit(f'Upstream asset differs from recorded hash: {asset}')
    bibliography = (paper.parent / 'references.bib').read_text()
    keys = set(re.findall(r'@\w+\{([^,]+),', bibliography))
    for group in re.findall(r'\\cite\{([^}]+)\}', text):
        if not set(group.split(',')) <= keys:
            raise SystemExit(f'Unknown citation: {group}')
    if args.pdf:
        info = subprocess.check_output(['pdfinfo', str(args.pdf)], text=True)
        pages = re.search(r'^Pages:\s+(\d+)', info, re.M)
        if not pages or int(pages[1]) > config['initial_max_pages']:
            raise SystemExit('PDF exceeds recorded initial page limit or is unreadable')
        size = re.search(r'^Page size:\s+([\d.]+) x ([\d.]+)', info, re.M)
        if not size or abs(float(size[1]) - 612) > 1 or abs(float(size[2]) - 792) > 1:
            raise SystemExit('Expected US letter page size')
        author = re.search(r'^Author:[ \t]*(.*)$', info, re.M)
        if author and author[1].strip():
            raise SystemExit('Remove PDF Author metadata for anonymous review')
        fonts = subprocess.check_output(['pdffonts', str(args.pdf)], text=True)
        for row in fonts.splitlines()[2:]:
            fields = row.split()
            if len(fields) >= 7 and fields[-5] != 'yes':
                raise SystemExit('PDF has a nonembedded font')
        print(f'PDF: {pages[1]} pages, letter size; checked font embedding and Author field')
    print('Selected local checks passed. Scientific review, full anonymity audit, AI disclosure')
    print('placement and official portal PDF validation remain required. Status:', config['readiness'])


if __name__ == '__main__':
    main()
