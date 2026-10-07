from pathlib import Path
import csv,hashlib,json,math,os,subprocess
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/wokwi'
OUT=ROOT/'verification/build'
OUT.mkdir(parents=True,exist_ok=True)
lock=json.loads((ROOT/'build_lock.json').read_text(encoding='utf-8'))
cfg=json.loads((ROOT/'src/config.json').read_text(encoding='utf-8'))
experiment=json.loads((ROOT/'experiment.json').read_text(encoding='utf-8'))
errors=[]
if cfg!=dict(experiment['baseline_config'],SYNTH_STRATEGY=experiment['synthesis_strategy']): errors.append('Non-strategy configuration drift')
for path,digest in experiment['immutable_files_sha256'].items():
    if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest: errors.append('Immutable file changed: '+path)
metrics={}
metrics_path=RUN/'final/metrics.csv'
if metrics_path.exists():
    for row in csv.DictReader(metrics_path.open()):
        try: metrics[row['Metric']]=float(row['Value'])
        except ValueError: metrics[row['Metric']]=row['Value']
else: errors.append('Final metrics missing')
resolved_path=RUN/'resolved.json'
resolved=json.loads(resolved_path.read_text()) if resolved_path.exists() else {}
source_hash=hashlib.sha256((ROOT/'src/project.v').read_bytes()).hexdigest()
if source_hash!=lock['source_sha256']: errors.append('v6 source changed')
# LibreLane serializes deprecated parameter names under their canonical names.
resolved_aliases={'FP_IO_HLENGTH': 'IO_PIN_H_LENGTH', 'FP_IO_VLENGTH': 'IO_PIN_V_LENGTH', 'FP_PDN_VPITCH': 'PDN_VPITCH', 'FP_PDN_MULTILAYER': 'PDN_MULTILAYER'}
expected={resolved_aliases.get(k,k):v for k,v in cfg.items()}
expected['PDK']='sky130A'
for k,v in expected.items():
    if resolved.get(k)!=v: errors.append('Resolved '+k+' differs')
if resolved.get('meta',{}).get('librelane_version')!=lock['librelane_version']: errors.append('LibreLane version differs')
pdk_source=None
sources=Path(resolved.get('PDK_ROOT','/nonexistent'))/'sky130A/SOURCES'
if sources.is_file():
    parts=sources.read_text().strip().split()
    if len(parts)==2: pdk_source,pdk_version=parts
    else: pdk_version=None
elif (RUN/'pdk.json').is_file():
    old=json.loads((RUN/'pdk.json').read_text())
    pdk_source,pdk_version=old.get('PDK_SOURCE'),old.get('PDK_VERSION')
else: pdk_version=None
if pdk_source!='open_pdks' or pdk_version!=lock['pdk_version']: errors.append('PDK source/version differs or unavailable')
tools_sha=None
if (ROOT/'tt/.git').exists():
    tools_sha=subprocess.check_output(['git','-C',str(ROOT/'tt'),'rev-parse','HEAD'],text=True).strip()
if tools_sha!=lock['support_tools_commit']: errors.append('Support tools version differs or unavailable')
def finite(value):return isinstance(value,(float,int)) and math.isfinite(value)
corners=[]
for name in lock['sta_corners']:
    def m(key):return metrics.get(key+'__corner:'+name)
    c={'corner':name,'setup_ns':m('timing__setup__ws'),'hold_ns':m('timing__hold__ws'),
       'slew':m('design__max_slew_violation__count'),
       'capacitance':m('design__max_cap_violation__count'),
       'fanout':m('design__max_fanout_violation__count')}
    c['timing_pass']=all(finite(c[k]) and c[k]>=0 for k in ('setup_ns','hold_ns'))
    c['electrical_pass']=all(finite(c[k]) and c[k]==0 for k in ('slew','capacitance','fanout'))
    corners.append(c)
physical={k:metrics.get(k) for k in ['magic__drc_error__count','design__lvs_error__count','route__drc_errors','antenna__violating__nets','antenna__violating__pins']}
physical_pass=all(finite(v) and v==0 for v in physical.values())
timing_pass=all(c['timing_pass'] for c in corners)
electrical_pass=all(c['electrical_pass'] for c in corners)
top=lock['top_module']
required=[RUN/'final/gds'/f'{top}.gds',RUN/'final/lef'/f'{top}.lef',
          RUN/'final/pnl'/f'{top}.pnl.v',metrics_path,resolved_path]
synth=list(RUN.glob('*-yosys-synthesis/reports/stat.rpt'))
complete=all(p.is_file() and p.stat().st_size for p in required) and len(synth)==1
ready=bool(complete and not errors)
# Strict checker failures can occur after a complete layout. Preserve its actual provenance.
if ready:
    pdk={'FLOW_NAME':'LibreLane','FLOW_VERSION':lock['librelane_version'],'PDK':'sky130A','PDK_SOURCE':pdk_source,'PDK_VERSION':pdk_version}
    (RUN/'pdk.json').write_text(json.dumps(pdk,indent=2))
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    workflow_url=os.environ.get('GITHUB_SERVER_URL','https://github.com')+'/'+os.environ.get('GITHUB_REPOSITORY','BarryLee911/tt-sky-ucl-project-v6')+'/actions/runs/'+os.environ.get('GITHUB_RUN_ID','local')
    provenance={'app':'Tiny Tapeout '+tools_sha,'repo':'https://github.com/BarryLee911/tt-sky-ucl-project-v6','commit':commit,'workflow_url':workflow_url}
    (RUN/'final/commit_id.json').write_text(json.dumps(provenance,indent=2))
worst=min((c for c in corners if finite(c['setup_ns'])),key=lambda c:c['setup_ns'],default=None)
if worst:
    reports=list(RUN.glob('*-openroad-stapostpnr/'+worst['corner']+'/max.rpt'))
    if reports:
        data=reports[-1].read_text()
        if 'Startpoint:' in data:
            first='Startpoint:'+data.split('Startpoint:',1)[1].split('Startpoint:',1)[0]
            (OUT/'worst_path.txt').write_text(first)
passed=bool(ready and timing_pass and electrical_pass and physical_pass)
synthesis_metrics={}
if synth:
    synthesis_state=synth[0].parents[1]/'state_out.json'
    if synthesis_state.is_file():
        synthesis_metrics=json.loads(synthesis_state.read_text()).get('metrics',{})
result={'experiment':experiment['id'],'synthesis_strategy':cfg['SYNTH_STRATEGY'],
        'baseline_commit':experiment['baseline_commit'],'resolved_aliases':resolved_aliases,'synthesis_metrics':synthesis_metrics,
        'immutable_files_sha256':experiment['immutable_files_sha256'],'status':'PASS' if passed else 'FAIL','source_sha256':source_hash,'clock_period_ns':cfg['CLOCK_PERIOD'],
        'provenance_errors':errors,'submission_ready':ready,'complete_layout':bool(complete),
        'timing_pass':timing_pass,'electrical_pass':electrical_pass,'physical_pass':physical_pass,
        'corners':corners,'physical':physical,'stdcell_area_um2':metrics.get('design__instance__area__stdcell'),
        'stdcell_count':metrics.get('design__instance__count__stdcell'),'metrics':metrics,'resolved':resolved,
        'pdk_source':pdk_source,'pdk_version':pdk_version,'support_tools_commit':tools_sha}
(OUT/'assessment.json').write_text(json.dumps(result,indent=2))
lines=['# SKY26d 80 MHz '+cfg['SYNTH_STRATEGY']+' experiment assessment','','Status: '+result['status'],
       'A completed layout may be packaged for testing even when strict timing/electrical checks fail.','',
       '| Corner | Setup ns | Hold ns | Slew | Cap | Fanout |','| --- | ---: | ---: | ---: | ---: | ---: |']
for c in corners:lines.append('| '+ ' | '.join(str(c[k]) for k in ['corner','setup_ns','hold_ns','slew','capacitance','fanout'])+' |')
lines+=['','Provenance errors: '+json.dumps(errors),'Physical checks: '+json.dumps(physical),
        'Stdcell area um2: '+str(result['stdcell_area_um2'])]
(OUT/'assessment.md').write_text('\n'.join(lines)+'\n')
if os.environ.get('GITHUB_OUTPUT'):
    with open(os.environ['GITHUB_OUTPUT'],'a') as f:
        f.write('submission_ready='+str(ready).lower()+'\npassed='+str(passed).lower()+'\n')
if os.environ.get('GITHUB_STEP_SUMMARY'):
    with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('resolved','metrics')},indent=2))

