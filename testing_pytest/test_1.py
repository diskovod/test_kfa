import pytest

@pytest.fixture

def smtp():
    import smtplib

    return smtplib.SMTP("merlinux.eu")
def test_ehlo(smtp):
    response, msg = smtp.ehlo()
    assert response == 250
    assert "merlinux" in msg
    assert 0 # for demo purposes