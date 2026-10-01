from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.test_api import VALID


def test_desk_scenario_and_result_rendering():
    page = AppTest.from_file(Path(__file__).resolve().parents[1] / "ui/app.py").run()
    assert not page.exception
    assert page.title[0].value == "Every ticket. A clearer next step."
    page.session_state["token"] = "explicit-ui-test-fixture"
    page.run()
    page.selectbox[0].select("Duplicate charge").run()
    assert page.text_input[0].value == "Charged twice for the same subscription"
    page.session_state["analyzed_subject"] = "Test fixture"
    page.session_state["result"] = {
        "triage": VALID,
        "metadata": {
            "provider": "local",
            "model": "test-fixture",
            "prompt_version": "triage-v1",
            "latency_ms": 100,
            "input_tokens": 10,
            "output_tokens": 20,
            "fallback_used": False,
            "schema_valid": True,
            "request_id": "test",
        },
    }
    page.run()
    assert not page.exception
    assert page.metric[0].value == "Billing"
    assert page.warning[0].value.startswith("Human review required")
