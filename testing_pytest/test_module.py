def test_ehlo(smtp):
    response = smtp.ehlo()
    assert response[0] == 250
    assert "merlinux" in response[1]
    assert 0 # for demo purposes
def test_noop(smtp):
    response = smtp.noop()
    assert response[0] == 250
    assert 0 # for demo purposes