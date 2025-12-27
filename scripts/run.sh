#!/bin/bash
uv run python -m  PZSA.services.frame_reader.read &
uv run python -m  PZSA.services.detection.detector.detect &
uv run python -m  PZSA.services.detection.violation_checker.check_violation &
uv run python -m PZSA.ui.app
