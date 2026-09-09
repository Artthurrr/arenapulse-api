from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def test_complete_player_flow(client: TestClient, auth_headers: dict[str, str]):
    games = client.get("/api/v1/games")
    assert games.status_code == 200
    game_id = games.json()[0]["id"]

    now = datetime.now(UTC)
    created = client.post(
        "/api/v1/challenges",
        headers=auth_headers,
        json={
            "title": "Fim de semana sem perder",
            "description": "Some pontos em partidas de EA Sports FC durante o fim de semana.",
            "reward": "Badge Invicto",
            "game_id": game_id,
            "starts_at": (now - timedelta(hours=1)).isoformat(),
            "ends_at": (now + timedelta(days=2)).isoformat(),
            "points_win": 3,
            "points_draw": 1,
            "points_loss": 0,
        },
    )
    assert created.status_code == 201
    challenge_id = created.json()["id"]

    joined = client.post(f"/api/v1/challenges/{challenge_id}/join", headers=auth_headers)
    assert joined.status_code == 201

    participations = client.get("/api/v1/me/participations", headers=auth_headers)
    assert participations.status_code == 200
    assert participations.json()[0]["challenge_id"] == challenge_id

    result = client.post(
        f"/api/v1/challenges/{challenge_id}/results",
        headers=auth_headers,
        json={"score_for": 3, "score_against": 1, "notes": "Virada no segundo tempo"},
    )
    assert result.status_code == 201
    assert result.json()["outcome"] == "win"
    assert result.json()["points_awarded"] == 3

    ranking = client.get(f"/api/v1/challenges/{challenge_id}/leaderboard")
    assert ranking.status_code == 200
    assert ranking.json()[0]["username"] == "player1"
    assert ranking.json()[0]["points"] == 3

    dashboard = client.get("/api/v1/me/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_wins"] == 1


def test_rejects_duplicate_registration(client: TestClient):
    payload = {"email": "same@example.com", "username": "sameuser", "password": "senha-forte"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409
