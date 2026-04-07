import json
import sys

import pytest

from ray.dashboard.modules.metrics.metrics_head import (
    DEFAULT_PROMETHEUS_HEADERS,
    parse_prom_headers,
)


@pytest.mark.parametrize(
    "headers, raises_error",
    [
        (DEFAULT_PROMETHEUS_HEADERS, False),
        ('{"H1": "V1", "H2": "V2"}', False),
        ('[["H1", "V1"], ["H2", "V2"], ["H2", "V3"]]', False),
        ('{"H1": "V1", "H2": ["V1", "V2"]}', True),
        ("not_json", True),
    ],
)
def test_parse_prom_headers(headers, raises_error):
    if raises_error:
        with pytest.raises(ValueError):
            parse_prom_headers(headers)
    else:
        result = parse_prom_headers(headers)
        assert result == json.loads(headers)


def test_stacked_panels_have_fill():
    """Stacked panels must have fill > 0 so stacking is visually apparent.
    The backpressure panel must not be stacked because backpressure time
    is not additive across concurrent operators."""
    from ray.dashboard.modules.metrics.grafana_dashboard_factory import (
        generate_data_grafana_dashboard,
    )

    dashboard = json.loads(generate_data_grafana_dashboard())
    panels_by_id = {p["id"]: p for p in dashboard["panels"]}

    # Backpressure panel (id=37): must NOT be stacked
    bp = panels_by_id[37]
    assert bp["stack"] is False, f"Backpressure panel should not be stacked, got {bp['stack']}"
    assert bp["fill"] == 0

    # Memory gauge panels: must be stacked with fill=2
    stacked_ids = {14, 16, 34, 35, 36}
    for pid in stacked_ids:
        p = panels_by_id[pid]
        assert p["stack"] is True, f"Panel {pid} ({p['title']}) should be stacked"
        assert p["fill"] == 2, f"Panel {pid} ({p['title']}) should have fill=2, got {p['fill']}"

    # All other panels should still have fill=0
    for p in dashboard["panels"]:
        if p["id"] not in stacked_ids and p["id"] != 37:
            if "fill" in p:
                assert p["fill"] == 0, f"Panel {p['id']} ({p['title']}) should have fill=0, got {p['fill']}"


if __name__ == "__main__":
    sys.exit(pytest.main(["-vv", __file__]))
