# Run end-to-end v2 to completion, then resume the halted v1 run.
# Started detached; each stage writes its own logs and DONE/FAILED marker.
$ErrorActionPreference = "Continue"
$wd = "C:\Users\joedicke\Documents\reps\EvoODE-next"
Set-Location $wd
$v2 = "$wd\experiments\annihilator_odebench_smoke\results_e2e_v2"
$v1 = "$wd\experiments\annihilator_odebench_smoke\results_e2e"
$chainLog = "$v2\chain.log"

"$(Get-Date -Format s) start v2" | Out-File -Append -Encoding utf8 $chainLog
& python -m experiments.annihilator_odebench_smoke.end2end --spec end2end_v2 --run --reuse-baselines-from experiments/annihilator_odebench_smoke/results_e2e --workers 7 --detach-marker 1> "$v2\main.out" 2> "$v2\main.err"
"$(Get-Date -Format s) v2 exit $LASTEXITCODE" | Out-File -Append -Encoding utf8 $chainLog

"$(Get-Date -Format s) start v1 resume" | Out-File -Append -Encoding utf8 $chainLog
& python -m experiments.annihilator_odebench_smoke.end2end --spec end2end_v1 --run --workers 7 --detach-marker 1> "$v1\resume.out" 2> "$v1\resume.err"
"$(Get-Date -Format s) v1 exit $LASTEXITCODE" | Out-File -Append -Encoding utf8 $chainLog
