# -*- coding: utf-8 -*-
#
#   Shared test setup
#
#   Puts converters/ on sys.path so the converters can be imported by name
#   (import diacritics2chao) when pytest is run from the repo root.
#
#   Also stubs flextoolslib so the module files themselves can be imported off
#   Windows: flextoolslib only installs alongside FieldWorks, but a module's
#   first statement is "from flextoolslib import *".
#

import importlib.util
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONVERTERS_PATH = REPO_ROOT / "converters"
sys.path.insert(0, str(CONVERTERS_PATH))


def _install_flextoolslib_stub():
    # The docs dict keys are plain constants in the real flextoolslib; their
    # values don't matter here, only that the names exist and stay distinct.
    if "flextoolslib" in sys.modules:
        return

    stub = types.ModuleType("flextoolslib")

    class FlexToolsModuleClass(object):
        def __init__(self, runFunction, docs):
            self.runFunction = runFunction
            self.docs = docs

        def GetDocs(self):
            return self.docs

    stub.FlexToolsModuleClass = FlexToolsModuleClass
    for name in ("FTM_Name", "FTM_Version", "FTM_ModifiesDB", "FTM_Synopsis",
                 "FTM_Help", "FTM_Description", "FTM_Path"):
        setattr(stub, name, name)

    # "from flextoolslib import *" honours __all__, so list everything a
    # module file needs
    stub.__all__ = ["FlexToolsModuleClass", "FTM_Name", "FTM_Version",
                    "FTM_ModifiesDB", "FTM_Synopsis", "FTM_Help",
                    "FTM_Description", "FTM_Path"]

    sys.modules["flextoolslib"] = stub


_install_flextoolslib_stub()


def _load_module_by_path(name, path):
    # FlexTools loads module files this way too (spec_from_file_location), so
    # the sys.path bootstrap in the module file behaves as it does in FlexTools
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def chao_module():
    """The Extract Chao tone letters FlexTools module, loaded by file path."""
    return _load_module_by_path(
        "Extract_Chao_tone_letters_from_tone_diacritics",
        REPO_ROOT / "Extract_Chao_tone_letters_from_tone_diacritics.py",
    )
