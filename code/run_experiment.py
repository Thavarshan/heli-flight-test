"""Validate and enumerate plans; flight execution is intentionally unavailable."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    cfg = json.loads(a.config.read_text())
    required = {'status', 'backend', 'methods',
                'seeds', 'simulation_calls_per_run'}
    if not required <= cfg.keys():
        p.error('configuration is missing required fields')
    if not cfg['methods'] or not cfg['seeds'] or cfg['simulation_calls_per_run'] <= 0:
        p.error('methods/seeds must be nonempty and budget positive')
    if not a.dry_run:
        p.error('flight execution unavailable: complete backend validation first')
    digest = hashlib.sha256(json.dumps(
        cfg, sort_keys=True).encode()).hexdigest()
    print(json.dumps({'status': 'PLAN_ONLY', 'configuration_sha256': digest,
                      'configuration': cfg,
                      'runs': len(cfg['methods']) * len(cfg['seeds'])}, indent=2))


if __name__ == '__main__':
    main()
