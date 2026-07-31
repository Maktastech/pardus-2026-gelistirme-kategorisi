import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../03-pardus-apt-doctor/src')))

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="apt_doctor_helper fcntl kullanir, sadece Linux'ta test edilir"
)

def test_apt_doctor_import():
    import apt_doctor_helper
    assert hasattr(apt_doctor_helper, "main")
