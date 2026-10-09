import os
import pytest
from services.report.generator import render_report

def test_template_render_english(tmp_path):
    facts = {
        "flood": {"flooded_area_km2": 38.4},
        "exposure": {
            "buildings_exposed_high": 142,
            "roads_exposed_length_m": 18600.0,
            "bridges_likely_damaged": 4
        },
        "cutoff": {"isolated_settlements": 4}
    }
    
    html_file = render_report("test-job-en", "2026-08-26", facts, lang="en")
    assert os.path.exists(html_file)
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Flood Situation Report" in content
    assert "38.4" in content
    assert "142" in content
    assert "2026-08-26" in content

def test_template_render_nepali(tmp_path):
    facts = {
        "flood": {"flooded_area_km2": 38.4},
        "exposure": {
            "buildings_exposed_high": 142,
            "roads_exposed_length_m": 18600.0,
            "bridges_likely_damaged": 4
        },
        "cutoff": {"isolated_settlements": 4}
    }
    
    html_file = render_report("test-job-ne", "2026-08-26", facts, lang="ne")
    assert os.path.exists(html_file)
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "बाढी तथा पहिरो विपद् स्थिति प्रतिवेदन" in content
    assert "38.4" in content
    assert "१४२" in content or "142" in content
