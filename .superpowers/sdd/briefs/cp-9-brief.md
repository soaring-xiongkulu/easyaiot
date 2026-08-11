# Brief — CP-9: FlightHub + directory code path

## CRITICAL — NO NESTED SUBAGENTS
Leaf only when executed (另令).

## Goal
FlightHub config/live API shapes + directory key fields vs Python on shared DB. Real FlightHub account/drone = Part2.

## Oracle / Java
- `flighthub_source.py`, `camera.py` flighthub/directory routes
- `CameraFlighthubService`, `CameraController`

## Done when
- Config readable; missing creds → honest fail; directory fields explainable
- `logs/cp-9-flighthub-directory.json` + report

## Prereq
CP-1
