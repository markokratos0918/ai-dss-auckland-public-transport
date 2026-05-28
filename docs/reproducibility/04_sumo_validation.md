# Layer 4: SUMO Scenario Validation

Architecture position:

```text
Decision Engine -> SUMO -> Dashboard
```

## Purpose

SUMO is used as a selected scenario validation layer. It helps compare baseline, disruption, and intervention scenarios for selected routes or corridors.

It is not a full Auckland-wide transport network simulation.

## Current Small Outputs

```text
data/processed/sumo_scenarios.csv
data/processed/sumo_kpis.csv
data/processed/sumo_validation_results.csv
```

## Assessment 1 Alignment

This layer supports the proposal requirement for simulation-based validation by showing how decision recommendations can be tested in scenario form.

## Interpretation

Use the SUMO outputs to explain:

- What scenario was tested.
- Which KPI was compared.
- Whether the intervention scenario improves on the disruption scenario.
- What assumptions limit the scenario.

## Scope Limits

- SUMO is scenario validation only.
- Results should not be presented as proof of real-world deployment success.
- The dashboard can display saved SUMO outputs without requiring live SUMO execution.
