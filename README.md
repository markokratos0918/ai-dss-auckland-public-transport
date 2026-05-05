# AI-Driven Decision Support System for Auckland Public Transport Delay Prediction

## Overview

This capstone project develops a prototype decision-support system using Auckland Transport GTFS Realtime data, GTFS Static reference data, and Open-Meteo weather data to predict delays and generate actionable recommendations for transport operators.

## Current Milestone

- Layer 1: Data Sources
- Layer 2: Data Integration and Preprocessing

## Core Data Sources

1. Auckland Transport GTFS Realtime
   - Trip updates
   - Delays
   - Live service data

2. Auckland Transport GTFS Static
   - Routes
   - Stops
   - Trips
   - Schedules

3. Open-Meteo Weather Data
   - Rainfall
   - Temperature
   - Wind speed

## Initial Objectives

- Test GTFS Realtime access
- Download GTFS Static files
- Prepare Open-Meteo weather sample
- Perform sample EDA
- Build integrated transport-weather dataset

## Planned Core Modules

1. GTFS + GTFS Static + Open-Meteo Dataset
2. Prediction Model
3. Decision Engine
4. SUMO Validation Scenario
5. Dashboard
6. Final Report

## Tools

- Python
- Jupyter Notebook
- pandas
- XGBoost
- Streamlit
- SUMO
- GitHub

## Status

Project initialization completed.

## Current Progress

### Layer 1 – Data Sources

- GTFS Static (routes, trips, stops)
- GTFS Realtime API (Trip Updates)

### Layer 2 – Data Integration & Preprocessing

- JSON parsing and feature extraction
- Delay computation (seconds → minutes)
- Integration with GTFS static routes
- Data validation (99.92% match rate)

### Status

Data pipeline validated and ready for extension (Open_Meteo weather integration).

## Environment Setup

To reproduce this project:

```bash
conda create -n capstone-gtfs python=3.11 -y
conda activate capstone-gtfs
pip install -r requirements.txt

Create a .env file in the project root:

AT_API_KEY=your_api_key_here


Note: The `.env` file is not included in the repository for security reasons.

```
