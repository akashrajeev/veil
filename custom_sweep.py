"""Sweep all custom calendars under each public experiment budget."""
import json,time
from scenario_lab import run_scenario,BUDGETS

def main():
    rows=[];start=time.perf_counter()
    for budget in BUDGETS:
        completed=violations=invalid=0
        for bob in range(16):
            for alice in range(16):
                result=run_scenario(alice,bob,budget)
                completed += result['outcome']=='scheduled'
                violations += result['observer_metrics']['prefix_violation_cells']
                invalid += result['observer_metrics']['invalid_meetings']
                assert result['observer_metrics']['prefix_violation_cells']==0
                assert result['observer_metrics']['invalid_meetings']==0
        rows.append({'budget':budget,'actual_calendar_cases':256,'scheduled_actual_cases':completed,
                     'violation_cells_summed_across_replays':violations,'invalid_meetings':invalid})
    output={'scope':'all 256 four-window actual pairs; each run audits its resident-conditioned world class',
            'elapsed_seconds':time.perf_counter()-start,'rows':rows}
    print(json.dumps(output,indent=2))
if __name__=='__main__':main()
