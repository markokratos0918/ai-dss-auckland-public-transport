# Layer 3: Decision Engine

Last reviewed: 2026-06-26

Architecture position:

```text
AI-DSS Modeling / SHAP -> Decision Engine -> SUMO
```

## Purpose

This layer converts delay-risk categories into operational recommendation fields for review, reporting, SUMO scenario preparation, and the later Streamlit dashboard.

There are two kinds of decision evidence:

| Evidence type | Meaning | Main use |
| --- | --- | --- |
| Observed/reference risk | Risk created from actual delay records | Validation, training reference, comparison, and traceability |
| AI-predicted risk | Risk created by the AI model | Final dashboard decision support |

The earlier observed-risk Decision Engine audit remains valid. The newer AI-based Decision Engine output maps AI-DSS prediction probabilities into operator-facing recommendation fields.

## Required Local Inputs

```text
Observed/reference input:
data/processed/parquet/decision_engine_model_baseline.parquet

AI prediction input:
data/processed/parquet/ai_predictions_model_baseline.parquet
```

These files are generated local artifacts and should not be committed to GitHub.

## Command

```bash
python src/audit_decision_engine_outputs.py
```

## AI-Based Decision Support Output

Primary final dashboard source:

```text
data/processed/parquet/ai_decision_support_model_baseline.parquet
```

This file contains:

- AI-predicted risk.
- AI prediction probability.
- Predicted delay minutes.
- AI-based recommended action.
- Route, service, and weather context.
- Observed/reference risk for comparison.

AI recommendation fields:

```text
ai_delay_risk
ai_recommended_action
ai_confidence_band
ai_decision_basis
```

## Expected Small Outputs

```text
data/processed/summaries/ai_decision_recommendation_summary.csv
data/processed/summaries/ai_decision_route_recommendation_counts.csv
```

Observed/reference summaries may also exist for audit and traceability:

```text
data/processed/summaries/decision_recommendation_summary.csv
data/processed/summaries/decision_route_recommendation_counts.csv
```

## Audit Purpose

The observed/reference audit checks that delay-risk values map consistently to operational recommendations:

| Delay risk | Recommendation role |
| --- | --- |
| Low | No operational action |
| Medium | Monitor route conditions |
| High | Adjust service headway |
| Severe | Standby bus or supervisor review |

## Scope Limits

- The Decision Engine is a rule-based decision-support layer.
- It does not automate public transport operations.
- AI recommendations support human decision-makers and do not replace public transport planners or operators.
- The final dashboard should focus on AI-predicted risk and AI-based recommended action, while keeping observed/reference risk available for comparison and traceability.
