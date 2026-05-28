# Decision Engine Manifest

Last reviewed: 2026-05-28

## Scope

This manifest records the real Auckland GTFS-Realtime decision-engine outputs produced from Notebook 09. It is the traceability note for downstream decision-support modules and does not replace Notebook 09 as the real Auckland validation source.

This audit validates Decision Engine rule consistency and risk-to-action traceability. It does not validate machine-learning prediction accuracy; model evaluation belongs to the AI-DSS modeling module.

Notebook roles:

- `notebooks/05_decision_engine.ipynb`: Kaggle prototype decision-engine reference.
- `notebooks/09_validation_and_evaluation_realtimegtfs.ipynb`: Real Auckland GTFS-Realtime validation source.
- `notebooks/10_sumo_minimal_prototype.ipynb`: Reserved for the SUMO minimal prototype.

Replication command:

```bash
python src/audit_decision_engine_outputs.py
```

Local input required:

- `data/processed/decision_engine_output.csv` must exist locally. It is a large Notebook 09 output and should not be committed to GitHub.

Outputs created:

- `docs/decision_engine_manifest.md`
- `data/processed/summaries/decision_recommendation_summary.csv`
- `data/processed/summaries/decision_route_recommendation_counts.csv`

## Source Outputs

| File | Rows | Role | Commit guidance |
| --- | --- | --- | --- |
| `data/processed/decision_engine_output.csv` | 2,529,972 | Full row-level real Auckland decision output | Local artifact; do not commit |
| `data/processed/intervention_logic.csv` | 4 | Risk-to-action rule mapping | Small output |
| `data/processed/summaries/gtfs_realtime_daily_summary.csv` | 22 | Daily operational summary | Small output |
| `data/processed/summaries/gtfs_realtime_route_daily_summary.csv` | 8,575 | Route-day operational summary | Small output |
| `data/processed/summaries/gtfs_realtime_top_delayed_routes.csv` | 20 | Top delayed routes summary | Small output |
| `data/processed/summaries/decision_recommendation_summary.csv` | 4 | Decision recommendation summary | Small output |
| `data/processed/summaries/decision_route_recommendation_counts.csv` | 1,493 | Route-level recommendation counts | Small output |

## Decision Logic

| Delay risk | Delay rule | Recommended action |
| --- | --- | --- |
| Low | 0 to 5 minutes absolute delay | No operational action required |
| Medium | More than 5 and up to 15 minutes absolute delay | Monitor route conditions |
| High | More than 15 and up to 25 minutes absolute delay | Adjust service headway |
| Severe | More than 25 minutes absolute delay | Deploy standby bus or supervisor review |

The recommendation language is decision support only. It does not represent automated control of services.

## Audit Result

| Check | Result |
| --- | --- |
| Decision output rows | 2,529,972 |
| Missing `delay_risk` | 0 |
| Missing `recommended_action` | 0 |
| Unique risk-to-action pairs | 4 |
| Recommendation-to-risk cardinality | 1 risk per recommendation |
| Risk-to-action traceability | 100% |

Recommendation distribution:

| Delay risk | Recommended action | Records | Share |
| --- | --- | --- | --- |
| Low | No operational action required | 1,965,777 | 77.70% |
| Medium | Monitor route conditions | 525,781 | 20.78% |
| High | Adjust service headway | 28,826 | 1.14% |
| Severe | Deploy standby bus or supervisor review | 9,588 | 0.38% |

## Downstream Use

The current decision-engine output is valid enough for downstream decision-support presentation. Later dashboard modules should use summary files where possible:

- Use `decision_recommendation_summary.csv` for overall recommendation distribution.
- Use `decision_route_recommendation_counts.csv` for route-level action counts.
- Use `gtfs_realtime_daily_summary.csv`, `gtfs_realtime_route_daily_summary.csv`, and `gtfs_realtime_top_delayed_routes.csv` for operational overview pages.
- Avoid loading `decision_engine_output.csv` by default because it is a large local artifact.

## GitHub Reproducibility

Commit the audit script, this manifest, and the small summary CSVs. Do not commit `data/processed/decision_engine_output.csv`. A future examiner can place the local decision output at the expected path and run the replication command above to create the same audit evidence.

## Remaining Risks

- The 30-day GTFS-Realtime collection is still continuing, so this remains a frozen 21/22-day baseline until the final collection window is validated.
- Some route metadata remains blank for S-prefix or special routes. Downstream presentation layers should label blank route names clearly.
- Notebook 09 should remain the source of truth for real Auckland validation. Do not create a separate decision-engine notebook unless a later module needs new analysis that cannot be represented by a manifest and summary outputs.
