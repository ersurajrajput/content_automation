#!/usr/bin/env python3
"""
Video Automator — launcher script.

Usage:
    python3 run.py

Make sure the .venv is active or PySide6 is installed:
    source .venv/bin/activate
    python3 run.py
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_automator.app import main

if __name__ == "__main__":
    main()
