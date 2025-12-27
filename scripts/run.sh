#!/bin/bash
uv run python -m  PZSA.services.frame_reader.src.read &
uv run python -m  PZSA.services.detection.detector.src.detect &
uv run python -m  PZSA.services.detection.violation_checker.src.check_violation &
uv run python -m PZSA.ui.src.app
