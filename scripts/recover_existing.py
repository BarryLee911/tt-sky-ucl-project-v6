from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path.cwd()
RUN = ROOT/'runs/wokwi'
lock = json.loads((ROOT/'build_lock.json').read_text())
profile = json.loads((ROOT/'experiment.json').read_text())
cfg = json.loads((ROOT/'src/config.json').read_text())
resolved = json.loads((RUN/'resolved.json').read_text())
old = json.loads((ROOT/'verification/build/assessment.json').read_text())
aliases = {'FP_IO_HLENGTH':'IO_PIN_H_LENGTH', 'FP_IO_VLENGTH':'IO_PIN_V_LENGTH',
           'FP_PDN_VPITCH':'PDN_VPITCH', 'FP_PDN_MULTILAYER':'PDN_MULTILAYER'}
expected = {aliases.get(k,k):v for k,v in cfg.items()}
expected['PDK'] = 'sky130A'
errors = ['Resolved '+k+' differs' for k,v in expected.items() if resolved.get(k)!=v]
assert not errors, errors
assert cfg == dict(profile['baseline_config'], SYNTH_STRATEGY=profile['synthesis_strategy'])
assert cfg['CLOCK_PERIOD']==12.5 and cfg['MAX_TRANSITION_CONSTRAINT']==0.75 and cfg['MAX_FANOUT_CONSTRAINT']==10
for path,digest in profile['immutable_files_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest, path
assert old['provenance_errors'] == ['Resolved '+k+' differs' for k in aliases]
assert old['complete_layout'] and old['source_sha256']==lock['source_sha256']
assert old['pdk_source']=='open_pdks' and old['pdk_version']==lock['pdk_version']
assert resolved['meta']['librelane_version']==lock['librelane_version']
tools_sha = subprocess.check_output(['git','-C','tt','rev-parse','HEAD'], text=True).strip()
assert tools_sha==lock['support_tools_commit']==old['support_tools_commit']
assert os.environ['SOURCE_COMMIT']==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert resolved==old['resolved']

out = ROOT/'verification/recovery'
out.mkdir(parents=True,exist_ok=True)
(out/'original_assessment.json').write_text(json.dumps(old,indent=2))
corrected = dict(old)
corrected.update(provenance_errors=[], submission_ready=True,
                 original_provenance_errors=old['provenance_errors'], resolved_aliases=aliases,
                 source_commit=os.environ['SOURCE_COMMIT'], original_run_id=int(os.environ['SOURCE_RUN_ID']),
                 recovery_run_url=os.environ['GITHUB_SERVER_URL']+'/'+os.environ['GITHUB_REPOSITORY']+'/actions/runs/'+os.environ['GITHUB_RUN_ID'])
assert corrected['status']=='FAIL' and not corrected['timing_pass'] and not corrected['electrical_pass']
(out/'assessment.json').write_text(json.dumps(corrected,indent=2))
pdk = {'FLOW_NAME':'LibreLane','FLOW_VERSION':lock['librelane_version'],'PDK':'sky130A',
       'PDK_SOURCE':old['pdk_source'],'PDK_VERSION':old['pdk_version']}
(RUN/'pdk.json').write_text(json.dumps(pdk,indent=2))
original_url = 'https://github.com/'+os.environ['GITHUB_REPOSITORY']+'/actions/runs/'+os.environ['SOURCE_RUN_ID']
provenance = {'app':'Tiny Tapeout '+tools_sha,'repo':'https://github.com/'+os.environ['GITHUB_REPOSITORY'],
              'commit':os.environ['SOURCE_COMMIT'],'workflow_url':original_url}
(RUN/'final/commit_id.json').write_text(json.dumps(provenance,indent=2))
top = lock['top_module']
fingerprints = {str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [RUN/'final/gds'/f'{top}.gds',RUN/'final/pnl'/f'{top}.pnl.v',RUN/'final/metrics.csv']}
(out/'unchanged_artifact_sha256.json').write_text(json.dumps(fingerprints,indent=2))
print(json.dumps({'strategy':cfg['SYNTH_STRATEGY'],'alias_audit':'PASS','status':corrected['status'],
                  'timing_pass':corrected['timing_pass'],'electrical_pass':corrected['electrical_pass'],
                  'source_commit':os.environ['SOURCE_COMMIT'],'original_run':original_url},indent=2))
with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as summary:
    summary.write('Reuses the original completed GDS; no synthesis or place-and-route.\n\n')
    summary.write('Legacy parameter aliases verified. Original strict timing/electrical status remains FAIL.\n')
