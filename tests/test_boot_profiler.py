import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../06-pardus-boot-profiler/src')))

from ayristirma import sureyi_saniyeye_cevir

def test_sureyi_saniyeye_cevir():
    assert sureyi_saniyeye_cevir("1h 2min 3s") == 3600 + 120 + 3
    assert sureyi_saniyeye_cevir("500ms") == 0.5
    assert sureyi_saniyeye_cevir("1min 10.5s") == 70.5
