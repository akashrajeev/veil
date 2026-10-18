"""One-command local verification. No server, account, API key or npm needed."""
import argparse,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).parent
UNIT=['test_mcp','test_server','test_http','test_invariants','test_secret_functions','test_evidence','test_ledger_schema','test_audit_export','test_scenario_lab','test_policy_optimality','test_intents','test_protected_fact','test_dialog','test_dialog_store','test_preferences','test_prior_lab','test_availability','test_partition_cache','test_experiment_spec','test_alternatives','test_weighted_optimum','test_state_faults','test_ordinary_demo','test_truthful_queries','test_package_lab','test_metamorphic','test_offline_cli','test_restart_equivalence','test_verification_runner','test_joint','test_calendar_input']
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--timeout-seconds',type=int,default=180,help='per-job verification limit');p.add_argument('--full',action='store_true',help='also run original audience-sequence and weighted-audience sweeps; expanded/adaptive scripts are separate');args=p.parse_args()
    if args.timeout_seconds<1:p.error('--timeout-seconds must be positive')
    jobs=[['-m','unittest',*UNIT],['run_spike.py']]
    if args.full:jobs += [['audience_checks.py'],['extra_checks.py']]
    result=[]
    for job in jobs:
        started=time.perf_counter()
        try:
            done=subprocess.run([sys.executable,*job],cwd=ROOT,capture_output=True,text=True,timeout=args.timeout_seconds)
        except subprocess.TimeoutExpired:
            print(json.dumps({'command':['python3',*job],'passed':False,'error':'verification job timeout'}));return 124
        item={'command':['python3',*job],'return_code':done.returncode,'seconds':round(time.perf_counter()-started,3)}
        result.append(item)
        print(json.dumps(item),flush=True)
        if done.returncode:
            print(done.stdout);print(done.stderr,file=sys.stderr);return done.returncode
        print(done.stderr[-1000:],file=sys.stderr)
    print(json.dumps({'passed':True,'jobs':result},indent=2));return 0
if __name__=='__main__':sys.exit(main())
