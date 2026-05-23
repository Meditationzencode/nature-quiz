import os
import random
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session

load_dotenv()
try:
    from questions import questions, birds, trees, insects, animals
except Exception:
    questions = birds = trees = insects = animals = []

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-fallback")

QUESTIONS_PER_GAME = 10
CATEGORIES = {
    "All": questions,
    "Birds": birds,
    "Trees": trees,
    "Insects": insects,
    "Animals": animals,
}
DIFFICULTY_TIMERS = {
    "Easy": 15,
    "Medium": 10,
    "Hard": 5,
}
DIFFICULTY_POINTS = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3,
}

DB_PATH = Path(__file__).parent / "scores.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage INTEGER NOT NULL,
                difficulty TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start", methods=["GET", "POST"])
def start_quiz():
    if request.method == "POST":
        difficulty = request.form.get("difficulty")
        if difficulty not in DIFFICULTY_TIMERS:
            return redirect(url_for("start_quiz"))
        session["time_limit"] = DIFFICULTY_TIMERS[difficulty]
        session["difficulty"] = difficulty
        return redirect(url_for("choose_category"))
    return render_template(
        "difficulty.html",
        difficulty_timers=DIFFICULTY_TIMERS,
        difficulty_points=DIFFICULTY_POINTS
    )


@app.route("/category", methods=["GET", "POST"])
def choose_category():
    if not session.get("time_limit"):
        return redirect(url_for("start_quiz"))

    if request.method == "POST":
        category = request.form.get("category", "All")

        if category not in CATEGORIES:
            return redirect(url_for("choose_category"))

        pool = CATEGORIES[category]

        if not pool:
            return render_template("500.html"), 500

        selected_questions = [
            {**q, "choices": random.sample(q["choices"], len(q["choices"]))}
            for q in random.sample(pool, min(QUESTIONS_PER_GAME, len(pool)))
        ]

        session["selected_questions"] = selected_questions
        session["current_question"] = 0
        session["score"] = 0
        session["feedback"] = None
        session["streak"] = 0
        session["best_streak"] = 0
        session["score_saved"] = False
        session["category"] = category

        return redirect(url_for("quiz"))

    return render_template("category.html")


@app.route("/quiz")
def quiz():
    selected_questions = session.get("selected_questions")
    current_question = session.get("current_question", 0)
    feedback = session.get("feedback")

    if not selected_questions:
        return redirect(url_for("home"))

    if current_question >= len(selected_questions):
        return redirect(url_for("result"))

    question = selected_questions[current_question]

    return render_template(
        "quiz.html",
        question=question,
        question_number=current_question + 1,
        total_questions=len(selected_questions),
        feedback=feedback,
        time_limit=session.get("time_limit", 15),
        streak=session.get("streak", 0),
        score=session.get("score", 0)
    )


@app.route("/answer", methods=["POST"])
def answer():
    selected_questions = session.get("selected_questions")
    current_question = session.get("current_question", 0)

    if not selected_questions:
        return redirect(url_for("home"))

    if current_question >= len(selected_questions):
        return redirect(url_for("result"))

    if session.get("feedback"):
        return redirect(url_for("quiz"))

    chosen_answer = request.form.get("answer")
    question = selected_questions[current_question]

    if not chosen_answer or chosen_answer not in question["choices"]:
        return redirect(url_for("quiz"))

    correct_answer = question["answer"]
    is_correct = chosen_answer == correct_answer

    if is_correct:
        session["score"] = session.get("score", 0) + 1
        streak = session.get("streak", 0) + 1
        session["streak"] = streak
        session["best_streak"] = max(streak, session.get("best_streak", 0))
    else:
        session["streak"] = 0

    session["feedback"] = {
        "selected": chosen_answer,
        "correct": correct_answer,
        "is_correct": is_correct
    }

    return redirect(url_for("quiz"))


@app.route("/next", methods=["POST"])
def next_question():
    selected_questions = session.get("selected_questions")
    if not selected_questions:
        return redirect(url_for("home"))

    current_question = session.get("current_question", 0)
    if current_question >= len(selected_questions):
        return redirect(url_for("result"))

    session["current_question"] = current_question + 1
    session["feedback"] = None

    return redirect(url_for("quiz"))


@app.route("/timeout", methods=["POST"])
def timeout():
    selected_questions = session.get("selected_questions")
    if not selected_questions:
        return redirect(url_for("home"))

    if session.get("feedback"):
        return redirect(url_for("quiz"))

    current_question = session.get("current_question", 0)

    if current_question >= len(selected_questions):
        return redirect(url_for("result"))

    correct_answer = selected_questions[current_question]["answer"]
    session["streak"] = 0
    session["feedback"] = {
        "selected": None,
        "correct": correct_answer,
        "is_correct": False,
        "timed_out": True
    }

    return redirect(url_for("quiz"))


@app.route("/result")
def result():
    selected_questions = session.get("selected_questions", [])
    score = session.get("score", 0)
    total_questions = len(selected_questions)

    if total_questions == 0:
        return redirect(url_for("home"))

    percentage = round((score / total_questions) * 100)
    points_per_answer = DIFFICULTY_POINTS.get(session.get("difficulty"), 1)
    points = score * points_per_answer
    total_points = total_questions * points_per_answer

    if percentage == 100:
        message = "Perfect score! Nature expert!"
    elif percentage >= 80:
        message = "Amazing job! You know your nature facts."
    elif percentage >= 60:
        message = "Nice work! You did really well."
    elif percentage >= 40:
        message = "Good try! Keep exploring nature."
    else:
        message = "Nice effort! Try again and beat your score."

    return render_template(
        "result.html",
        score=score,
        total_questions=total_questions,
        percentage=percentage,
        points=points,
        total_points=total_points,
        message=message,
        best_streak=session.get("best_streak", 0),
        score_saved=session.get("score_saved", False)
    )


@app.route("/save_score", methods=["POST"])
def save_score():
    name = request.form.get("name", "").strip()[:20]
    if not name:
        return redirect(url_for("result"))

    selected_questions = session.get("selected_questions", [])
    total = len(selected_questions)
    if total == 0:
        return redirect(url_for("home"))

    if session.get("score_saved"):
        return redirect(url_for("leaderboard"))

    score = session.get("score", 0)
    percentage = round((score / total) * 100)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO scores (name, score, total, percentage, difficulty, category) VALUES (?, ?, ?, ?, ?, ?)",
            (name, score, total, percentage, session.get("difficulty"), session.get("category"))
        )

    session["score_saved"] = True

    return redirect(url_for("leaderboard"))


@app.route("/leaderboard")
def leaderboard():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        scores = conn.execute(
            """
            SELECT *,
                score * CASE difficulty
                    WHEN 'Hard' THEN 3
                    WHEN 'Medium' THEN 2
                    ELSE 1
                END AS points
            FROM scores
            ORDER BY points DESC, percentage DESC, created_at ASC
            LIMIT 10
            """
        ).fetchall()
    return render_template("leaderboard.html", scores=scores)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)
