# -*- coding: utf-8 -*-
#
#   Shared test setup for the zhire project
#
#   Puts this project's converters/ on sys.path so the converters can be
#   imported by name (import phonemic2orthography), and puts the repo's
#   shared tests/ directory on sys.path so the approval-testing harness in
#   tests/approval.py can be imported the same way.
#

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT / "converters"))
sys.path.insert(0, str(REPO_ROOT / "tests"))
