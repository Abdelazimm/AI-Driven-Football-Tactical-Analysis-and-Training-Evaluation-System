"""Read-only presentation routes serve only verified existing evidence."""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_showcase_response_uses_frozen_cases():
    response = TestClient(app).get("/api/v1/showcase")
    assert response.status_code == 200
    data = response.json()
    assert data["showcase_mode"] == "ORACLE_ASSISTED_CAPABILITY_DEMONSTRATION"
    assert {card["id"] for card in data["cards"]} == {
        "C03_HOLD_POSITION", "C04_DEFENSIVE_MARKING", "C06_PRESSING"
    }
    assert data["scientific_automated_status"] == "FAIL_HIGH_FRAGMENTATION"


def test_showcase_media_types_and_range_support():
    client = TestClient(app)
    for case, media_type in [("C03", "video/mp4"), ("C04", "image/png"), ("C06", "video/mp4")]:
        response = client.get(f"/api/v1/showcase/media/{case}", headers={"Range": "bytes=0-0"})
        assert response.status_code == 206
        assert response.headers["content-type"] == media_type
        assert response.content and len(response.content) == 1
    assert client.get("/api/v1/showcase/media/unknown").status_code == 404
