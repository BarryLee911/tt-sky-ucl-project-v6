from pathlib import Path
from decimal import Decimal
import hashlib,json,re,sys
import yaml
ROOT=Path(__file__).resolve().parents[1]
lock=json.loads((ROOT/'build_lock.json').read_text(encoding='utf-8'))
config=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'))
info=yaml.safe_load((ROOT/'info.yaml').read_text(encoding='utf-8'))['project']
experiment=json.loads((ROOT/'experiment.json').read_text(encoding='utf-8'))
assert experiment['baseline_commit']=='45e7d83f2bea6b98df407d108c6f1fffc6f5cbe6'
strategy=experiment['synthesis_strategy']
assert strategy in ('AREA 0','DELAY 0')
assert experiment['id']=={'AREA 0':'area0','DELAY 0':'delay0'}[strategy]
assert config==dict(experiment['baseline_config'],SYNTH_STRATEGY=strategy), 'Non-strategy configuration drift'
assert info['clock_hz']==80000000 and info['tiles']=='6x2'
for path,digest in experiment['immutable_files_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest, 'Immutable file changed: '+path
source=(ROOT/'src/project.v').read_bytes()
assert hashlib.sha256(source).hexdigest()==lock['source_sha256'], 'v6 RTL bytes changed'
assert info['clock_hz'] in (40000000,80000000)
period=Decimal(str(config['CLOCK_PERIOD']))
assert period*info['clock_hz']==Decimal('1000000000'), 'info.yaml clock differs'
assert period*Decimal(str(config['IO_DELAY_CONSTRAINT']))/100==Decimal('2.5')
assert info['top_module']==lock['top_module']
assert info['source_files']==['project.v','sky_wrapper.v']
assert info['tiles'] in ('4x2','6x2','8x2')
expected={'SYNTH_STRATEGY':strategy,'STD_CELL_LIBRARY':'sky130_fd_sc_hd',
          'PL_TARGET_DENSITY_PCT':60,'FP_CORE_UTIL':50,
          'MAX_TRANSITION_CONSTRAINT':0.75,'MAX_FANOUT_CONSTRAINT':10,
          'MAX_CAPACITANCE_CONSTRAINT':None,
          'PL_RESIZER_HOLD_SLACK_MARGIN':0.1,'GRT_RESIZER_HOLD_SLACK_MARGIN':0.05,
          'TIMING_VIOLATION_CORNERS':['*'],'HOLD_VIOLATION_CORNERS':['*'],
          'MAX_SLEW_VIOLATION_CORNERS':['*'],'MAX_CAP_VIOLATION_CORNERS':['*']}
assert all(config.get(k)==v for k,v in expected.items()), 'Experiment constraints changed'
assert config['STA_CORNERS']==lock['sta_corners']
assert b'parameter integer HANDOFF_WAIT_CYCLES = 80000' in source
workflow=yaml.safe_load((ROOT/'.github/workflows/gds.yaml').read_text(encoding='utf-8'))
steps=workflow['jobs']['gds']['steps']
harden=next(s for s in steps if s.get('id')=='harden')
assert harden['uses'].endswith('@'+lock['action_commit'])
assert harden['with']=={'pdk':'sky130A','tools-ref':lock['support_tools_commit'],'librelane-version':lock['librelane_version']}
report={'status':'PASS','experiment':experiment['id'],'synthesis_strategy':strategy,'baseline_commit':experiment['baseline_commit'],'clock_hz':info['clock_hz'],'clock_period_ns':float(period),
        'io_delay_ns':2.5,'tiles':info['tiles'],'source_sha256':lock['source_sha256'],
        'handoff_cycles':80000,'handoff_ms':80000/info['clock_hz']*1000,
        'frequencies_hz':{str(level):info['clock_hz']/(2048*(2**level)) for level in range(24)}}
out=ROOT/'verification'
out.mkdir(exist_ok=True)
(out/'inputs.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='frequencies_hz'},indent=2))

