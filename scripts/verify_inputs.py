"""Source/configuration provenance checks; no timing or electrical signoff policy."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
lock = json.loads((ROOT / 'build_lock.json').read_text(encoding='utf-8'))
config = json.loads((ROOT / 'src/config.json').read_text(encoding='utf-8'))
info = yaml.safe_load((ROOT / 'info.yaml').read_text(encoding='utf-8'))['project']
experiment = json.loads((ROOT / 'experiment.json').read_text(encoding='utf-8'))
assert experiment['id'] == 'official-checks-4x2'
assert experiment['baseline_commit'] == '679dbd88bb4a0062b3611c912f4d5e878e2e3574'
assert experiment['acceptance_profile'] == 'official-ttsky26d-defaults'
assert experiment['removed_config_keys'] == []
assert experiment['config_overrides'] == {}
assert config == experiment['baseline_config'], 'Implementation configuration changed'
assert not {'TIMING_VIOLATION_CORNERS', 'HOLD_VIOLATION_CORNERS',
            'MAX_SLEW_VIOLATION_CORNERS', 'MAX_CAP_VIOLATION_CORNERS',
            'SETUP_VIOLATION_CORNERS'} & config.keys()
assert experiment['baseline_tiles'] == '6x2' and experiment['tiles'] == '4x2'
info_text = (ROOT / 'info.yaml').read_text(encoding='utf-8')
assert info_text.count('tiles: "4x2"') == 1
baseline_info = info_text.replace('tiles: "4x2"', 'tiles: "6x2"')
assert hashlib.sha256(baseline_info.encode()).hexdigest() == experiment['baseline_info_yaml_sha256']
assert hashlib.sha256((ROOT / 'build_lock.json').read_bytes()).hexdigest() == experiment['build_lock_sha256']
for path, expected_hash in experiment['immutable_files_sha256'].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected_hash, path
source = (ROOT / 'src/project.v').read_bytes()
assert hashlib.sha256(source).hexdigest() == lock['source_sha256']
assert b'parameter integer HANDOFF_WAIT_CYCLES = 80000' in source
assert info['clock_hz'] == 80000000 and info['tiles'] == '4x2'
assert info['top_module'] == lock['top_module']
assert info['source_files'] == ['project.v', 'sky_wrapper.v']
period = Decimal(str(config['CLOCK_PERIOD']))
assert period * info['clock_hz'] == Decimal('1000000000')
assert period * Decimal(str(config['IO_DELAY_CONSTRAINT'])) / 100 == Decimal('2.5')
assert config['STA_CORNERS'] == lock['sta_corners']
workflow = yaml.safe_load((ROOT / '.github/workflows/gds.yaml').read_text(encoding='utf-8'))
gds = workflow['jobs']['gds']
assert len(gds['steps']) == 2
harden = next(step for step in gds['steps'] if step.get('id') == 'harden')
assert harden['uses'] == 'TinyTapeout/tt-gds-action@' + lock['action_commit']
assert harden['with'] == {'pdk': 'sky130A', 'tools-ref': lock['support_tools_commit'],
                          'librelane-version': lock['librelane_version']}
assert 'continue-on-error' not in harden and 'continue-on-error' not in gds
for name in ('precheck', 'gl_test'):
    job = workflow['jobs'][name]
    assert job['needs'] == 'gds' and 'if' not in job
report = {'status': 'PASS', 'scope': 'source and configuration provenance only',
          'experiment': experiment['id'], 'baseline_commit': experiment['baseline_commit'],
          'acceptance_profile': experiment['acceptance_profile'],
          'clock_hz': info['clock_hz'], 'clock_period_ns': float(period),
          'io_delay_ns': 2.5, 'tiles': info['tiles'], 'source_sha256': lock['source_sha256'],
          'handoff_cycles': 80000, 'handoff_ms': 1.0,
          'tile_change': {'from': experiment['baseline_tiles'], 'to': info['tiles']}}
out = ROOT / 'verification'
out.mkdir(exist_ok=True)
(out / 'inputs.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
