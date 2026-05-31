import sqlite3

import app as quiz_app
from helpers import start_quiz


# Basic pages

def test_home_loads(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Nature Quiz" in r.data


def test_difficulty_page_loads(client):
    r = client.get("/start")
    assert r.status_code == 200
    assert b"Choose Difficulty" in r.data
    assert b"Easy" in r.data
    assert b"Medium" in r.data
    assert b"Hard" in r.data
    assert b"15 seconds, 1 point per correct answer" in r.data
    assert b"10 seconds, 2 points per correct answer" in r.data
    assert b"5 seconds, 3 points per correct answer" in r.data


def test_404_returns_custom_page(client):
    r = client.get("/does-not-exist")
    assert r.status_code == 404
    assert b"404" in r.data


# Input validation

def test_invalid_difficulty_redirects_back(client):
    r = client.post("/start", data={"difficulty": "Extreme"})
    assert r.status_code == 302
    assert "/start" in r.headers["Location"]


def test_category_requires_difficulty_in_session(client):
    r = client.get("/category")
    assert r.status_code == 302
    assert "/start" in r.headers["Location"]


def test_invalid_category_redirects_back(client):
    client.post("/start", data={"difficulty": "Easy"})
    r = client.post("/category", data={"category": "Hackers"})
    assert r.status_code == 302
    assert "/category" in r.headers["Location"]


def test_spoofed_answer_rejected(client):
    start_quiz(client)
    r = client.post("/answer", data={"answer": "HACKED"}, follow_redirects=True)
    assert b"answer-form" in r.data


# Quiz flow

def test_quiz_starts_on_question_one(client):
    start_quiz(client)
    r = client.get("/quiz")
    assert r.status_code == 200
    assert b"Q1 / 10" in r.data


def test_timeout_shows_feedback_with_correct_answer(client):
    start_quiz(client)
    r = client.post("/timeout", follow_redirects=True)
    assert b"Time" in r.data
    assert b"correct answer" in r.data


def test_answer_feedback_shows_explanation(client):
    with client.session_transaction() as sess:
        sess["selected_questions"] = [{
            "question": "Which insect makes honey?",
            "choices": ["Bee", "Ant", "Fly", "Wasp"],
            "answer": "Bee",
            "explanation": "Bees make honey from flower nectar and store it in honeycombs."
        }]
        sess["current_question"] = 0
        sess["score"] = 0
        sess["feedback"] = None
        sess["streak"] = 0
        sess["best_streak"] = 0

    r = client.post("/answer", data={"answer": "Bee"}, follow_redirects=True)

    assert b"Nature fact:" in r.data
    assert b"Bees make honey from flower nectar" in r.data


def test_review_page_shows_recorded_answers(client):
    with client.session_transaction() as sess:
        sess["selected_questions"] = [{
            "question": "Which insect makes honey?",
            "choices": ["Bee", "Ant", "Fly", "Wasp"],
            "answer": "Bee",
            "explanation": "Bees make honey from flower nectar and store it in honeycombs."
        }]
        sess["current_question"] = 0
        sess["score"] = 0
        sess["feedback"] = None
        sess["streak"] = 0
        sess["best_streak"] = 0

    client.post("/answer", data={"answer": "Bee"})
    r = client.get("/review")

    assert r.status_code == 200
    assert b"Review Answers" in r.data
    assert b"Which insect makes honey?" in r.data
    assert b"Bees make honey from flower nectar" in r.data


def test_double_submit_is_ignored(client):
    with client.session_transaction() as sess:
        sess["selected_questions"] = [{
            "question": "Which insect makes honey?",
            "choices": ["Bee", "Ant", "Fly", "Wasp"],
            "answer": "Bee"
        }]
        sess["current_question"] = 0
        sess["score"] = 0
        sess["feedback"] = None
        sess["streak"] = 0
        sess["best_streak"] = 0

    client.post("/answer", data={"answer": "Bee"})
    client.post("/answer", data={"answer": "Ant"})

    with client.session_transaction() as sess:
        assert sess["score"] == 1
        assert len(sess["answer_history"]) == 1
        assert sess["feedback"]["selected"] == "Bee"


def test_result_requires_session(client):
    r = client.get("/result")
    assert r.status_code == 302
    assert "/" in r.headers["Location"]


def test_result_page_shows_quiz_summary(client):
    with client.session_transaction() as sess:
        sess["selected_questions"] = [{
            "question": "Which insect makes honey?",
            "choices": ["Bee", "Ant", "Fly", "Wasp"],
            "answer": "Bee"
        }]
        sess["score"] = 1
        sess["difficulty"] = "Hard"
        sess["category"] = "Insects"
        sess["best_streak"] = 1

    r = client.get("/result")

    assert b"Difficulty" in r.data
    assert b"Hard" in r.data
    assert b"Category" in r.data
    assert b"Insects" in r.data


def test_calculate_points_uses_difficulty_values():
    assert quiz_app.calculate_points(5, "Easy") == 5
    assert quiz_app.calculate_points(5, "Medium") == 10
    assert quiz_app.calculate_points(5, "Hard") == 15
    assert quiz_app.calculate_points(5, "Unknown") == 5


def test_leaderboard_orders_by_points(client, tmp_path, monkeypatch):
    test_db = tmp_path / "scores.db"
    monkeypatch.setattr(quiz_app, "DB_PATH", test_db)
    quiz_app.init_db()

    with sqlite3.connect(test_db) as conn:
        conn.executemany(
            """
            INSERT INTO scores
                (name, score, total, percentage, points, difficulty, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("Easy Max", 10, 10, 100, 10, "Easy", "All", "2026-05-23 10:00:00"),
                ("Hard Try", 6, 10, 60, 18, "Hard", "All", "2026-05-23 11:00:00"),
            ]
        )

    r = client.get("/leaderboard")

    assert r.status_code == 200
    assert r.data.index(b"Hard Try") < r.data.index(b"Easy Max")


def test_leaderboard_filters_by_difficulty_and_category(client, tmp_path, monkeypatch):
    test_db = tmp_path / "scores.db"
    monkeypatch.setattr(quiz_app, "DB_PATH", test_db)
    quiz_app.init_db()

    with sqlite3.connect(test_db) as conn:
        conn.executemany(
            """
            INSERT INTO scores
                (name, score, total, percentage, points, difficulty, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("Hard Bird Score", 7, 10, 70, 21, "Hard", "Birds"),
                ("Easy Tree Score", 10, 10, 100, 10, "Easy", "Trees"),
            ]
        )

    r = client.get("/leaderboard?difficulty=Hard&category=Birds")

    assert r.status_code == 200
    assert b"Hard Bird Score" in r.data
    assert b"Easy Tree Score" not in r.data


# Health check + response headers

def test_healthz_returns_ok(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_security_headers_set_on_every_response(client):
    r = client.get("/")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Referrer-Policy"] == "same-origin"
    assert r.headers["X-Frame-Options"] == "DENY"


def test_request_id_is_echoed_back(client):
    r = client.get("/")
    rid = r.headers.get("X-Request-ID")
    assert rid and len(rid) == 8  # 4 bytes hex


def test_hsts_only_set_when_production(client, monkeypatch):
    # Off by default outside production
    r = client.get("/")
    assert "Strict-Transport-Security" not in r.headers

    # On when IS_PRODUCTION is set
    monkeypatch.setattr(quiz_app, "IS_PRODUCTION", True)
    r = client.get("/")
    assert "Strict-Transport-Security" in r.headers


# CSRF (default test client has testing=True which bypasses CSRF;
# these flip it off to exercise the real middleware).

def test_csrf_rejects_post_without_token():
    quiz_app.app.testing = False
    try:
        client = quiz_app.app.test_client()
        r = client.post("/start", data={"difficulty": "Easy"})
        assert r.status_code == 400
    finally:
        quiz_app.app.testing = True


def test_csrf_accepts_post_with_valid_token():
    quiz_app.app.testing = False
    try:
        client = quiz_app.app.test_client()
        client.get("/")  # issues a csrf_token into the session
        with client.session_transaction() as sess:
            token = sess["csrf_token"]
        r = client.post("/start", data={"difficulty": "Easy", "csrf_token": token})
        assert r.status_code == 302
    finally:
        quiz_app.app.testing = True


def test_score_can_only_be_saved_once(client, tmp_path, monkeypatch):
    test_db = tmp_path / "scores.db"
    monkeypatch.setattr(quiz_app, "DB_PATH", test_db)
    quiz_app.init_db()

    start_quiz(client)
    with client.session_transaction() as sess:
        sess["score"] = 5
        sess["difficulty"] = "Medium"

    client.post("/save_score", data={"name": "Brad"})
    client.post("/save_score", data={"name": "Brad"})

    with sqlite3.connect(test_db) as conn:
        saved_scores, points = conn.execute(
            "SELECT COUNT(*), points FROM scores"
        ).fetchone()

    assert saved_scores == 1
    assert points == 10
