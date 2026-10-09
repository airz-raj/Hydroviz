import pytest
from services.report.number_guard import normalise_devanagari_digits, extract_numbers, validate_numbers

def test_devanagari_digits_normalisation():
    # ०१२३४५६७८९ -> 0123456789
    nepali_str = "जलमग्न क्षेत्र ३८.४ वर्ग कि.मि. र १४२ घरहरू"
    normalized = normalise_devanagari_digits(nepali_str)
    assert "38.4" in normalized
    assert "142" in normalized

def test_number_guard_devanagari_validation():
    allowed_numbers = [38.4, 142.0]
    
    # Valid Nepali text with Devanagari numerals
    valid_nepali = "बाढीको कारण ३८.४ वर्ग कि.मि. क्षेत्र डुबानमा पर्यो र १४२ घर प्रभावित भए।"
    is_valid, offending = validate_numbers(valid_nepali, allowed_numbers)
    assert is_valid is True
    assert offending is None

    # Hallucinated Nepali text with Devanagari numeral ९९९ (999)
    fake_nepali = "बाढीको कारण ९९९ घर प्रभावित भए।"
    is_valid, offending = validate_numbers(fake_nepali, allowed_numbers)
    assert is_valid is False
    assert offending == "999"
