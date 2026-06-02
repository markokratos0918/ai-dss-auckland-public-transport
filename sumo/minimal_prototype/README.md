# SUMO Minimal Prototype

This folder contains the lightweight SUMO scenario-validation prototype for the Auckland public transport delay prediction project.

SUMO is used here as an added-value validation layer for a simplified one-route or one-corridor scenario. It is not a live operations engine and it is not a full Auckland network simulation.

Required interpretation:

> SUMO outputs are scenario-estimated impacts and do not prove real-world operational success.

## Local SUMO Environment

The local machine has SUMO available at:

```text
C:\Program Files (x86)\Eclipse\Sumo\
```

Observed version:

```text
Eclipse SUMO 1.26.0
```

Both `sumo` and `sumo-gui` are available locally.

## Intended Prototype Scope

The prototype will compare three scenarios:

1. Baseline Operations
2. Disruption Scenario
3. Intervention Scenario

The dashboard should read saved CSV outputs and should not require live SUMO execution.
