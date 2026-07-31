import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../05-pardus-log-doctor/src')))

from kurallar import kayit_yorumla

def test_oom_kill():
    res = kayit_yorumla("Out of memory: Killed process 1234")
    assert res is not None
    baslik, neden, cozum = res
    assert "Bellek yetersizliginden" in baslik

def test_io_error():
    res = kayit_yorumla("blk_update_request: I/O error, dev sda, sector 123")
    assert res is not None
    assert "Disk" in res[0]

def test_bilinmeyen_hata():
    res = kayit_yorumla("Normal bir sistem gunlugu mesaji, hata icermiyor")
    assert res is None
