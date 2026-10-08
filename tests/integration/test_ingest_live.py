import pytest

@pytest.mark.skip(reason="Live API tests require credentials and hit real endpoints")
def test_ingest_live():
    """
    (Gated) Full ingest on small bbox.
    In a real CI pipeline, this would use a tiny BBOX and check that CDSE
    returns valid data and our pipeline saves COGs successfully.
    """
    pass
