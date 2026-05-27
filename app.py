import os
import random
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from facts import get_explanation
from questions import questions, birds, trees, insects, animals

load_dotenv()

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
DIFFICULTY_FILTERS = ["All", *DIFFICULTY_TIMERS.keys()]
CATEGORY_FILTERS = list(CATEGORIES.keys())

DB_PATH = Path(__file__).parent / "scores.db"


def points_for_difficulty(difficulty):
    return DIFFICULTY_POINTS.get(difficulty, DIFFICULTY_POINTS["Easy"])


def calculate_points(score, difficulty):
    return score * points_for_difficulty(difficulty)


def valid_filter(value, allowed_values):
    return value if value in allowed_values else "All"


def build_answer_record(question, selected_answer, is_correct, timed_out=False):
    return {
        "question": question["question"],
        "selected": selected_answer,
        "correct": question["answer"],
        "is_correct": is_correct,
        "timed_out": timed_out,
        "explanation": get_explanation(question)
    }


def record_answer(record):
    session["answer_history"] = session.get("answer_history", []) + [record]


def start_new_game(category):
    """Reset all session state for a fresh game drawn from the given category."""
    pool = CATEGORIES[category]
    session["selected_questions"] = [
        {**q, "choices": random.sample(q["choices"], len(q["choices"]))}
        for q in random.sample(pool, min(QUESTIONS_PER_GAME, len(pool)))
    ]
    session["current_question"] = 0
    session["score"] = 0
    session["feedback"] = None
    session["streak"] = 0
    session["best_streak"] = 0
    session["score_saved"] = False
    session["answer_history"] = []
    session["category"] = category


def active_question():
    """Return ((questions, index), None) for the in-progress game, or
    (None, <redirect>) pointing where the request should bail out to."""
    selected_questions = session.get("selected_questions")
    if not selected_questions:
        return None, redirect(url_for("home"))

    current_question = session.get("current_question", 0)
    if current_question >= len(selected_questions):
        return None, redirect(url_for("result"))

    return (selected_questions, current_question), None


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage INTEGER NOT NULL,
                points INTEGER,
                difficulty TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        columns = [
            column[1]
            for column in conn.execute("PRAGMA table_info(scores)").fetchall()
        ]
        if "points" not in columns:
            conn.execute("ALTER TABLE scores ADD COLUMN points INTEGER")
            scores_without_points = conn.execute(
                "SELECT id, score, difficulty FROM scores"
            ).fetchall()
            conn.executemany(
                "UPDATE scores SET points = ? WHERE id = ?",
                [
                    (calculate_points(score, difficulty), score_id)
                    for score_id, score, difficulty in scores_without_points
                ]
            )

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

        if not CATEGORIES[category]:
            return render_template("500.html"), 500

        start_new_game(category)
        return redirect(url_for("quiz"))

    return render_template("category.html")


@app.route("/quiz")
def quiz():
    game, bail = active_question()
    if bail:
        return bail
    selected_questions, current_question = game

    return render_template(
        "quiz.html",
        question=selected_questions[current_question],
        question_number=current_question + 1,
        total_questions=len(selected_questions),
        feedback=session.get("feedback"),
        time_limit=session.get("time_limit", 15),
        streak=session.get("streak", 0),
        score=session.get("score", 0)
    )


@app.route("/answer", methods=["POST"])
def answer():
    game, bail = active_question()
    if bail:
        return bail
    selected_questions, current_question = game

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

    answer_record = build_answer_record(question, chosen_answer, is_correct)
    session["feedback"] = answer_record
    record_answer(answer_record)

    return redirect(url_for("quiz"))


@app.route("/next", methods=["POST"])
def next_question():
    game, bail = active_question()
    if bail:
        return bail
    _, current_question = game

    session["current_question"] = current_question + 1
    session["feedback"] = None

    return redirect(url_for("quiz"))


@app.route("/timeout", methods=["POST"])
def timeout():
    game, bail = active_question()
    if bail:
        return bail
    selected_questions, current_question = game

    if session.get("feedback"):
        return redirect(url_for("quiz"))

    session["streak"] = 0
    answer_record = build_answer_record(
        selected_questions[current_question],
        None,
        False,
        timed_out=True
    )
    session["feedback"] = answer_record
    record_answer(answer_record)

    return redirect(url_for("quiz"))


@app.route("/result")
def result():
    selected_questions = session.get("selected_questions", [])
    score = session.get("score", 0)
    total_questions = len(selected_questions)

    if total_questions == 0:
        return redirect(url_for("home"))

    percentage = round((score / total_questions) * 100)
    difficulty = session.get("difficulty")
    points = calculate_points(score, difficulty)
    total_points = calculate_points(total_questions, difficulty)

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
        difficulty=difficulty,
        category=session.get("category", "All"),
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
    points = calculate_points(score, session.get("difficulty"))

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO scores
                (name, score, total, percentage, points, difficulty, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                score,
                total,
                percentage,
                points,
                session.get("difficulty"),
                session.get("category")
            )
        )

    session["score_saved"] = True

    return redirect(url_for("leaderboard"))


@app.route("/leaderboard")
def leaderboard():
    active_difficulty = valid_filter(
        request.args.get("difficulty", "All"),
        DIFFICULTY_FILTERS
    )
    active_category = valid_filter(
        request.args.get("category", "All"),
        CATEGORY_FILTERS
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        saved_scores = conn.execute(
            """
            SELECT * FROM scores
            WHERE (? = 'All' OR difficulty = ?)
              AND (? = 'All' OR category = ?)
            ORDER BY points DESC, percentage DESC, created_at ASC
            LIMIT 10
            """,
            (active_difficulty, active_difficulty, active_category, active_category)
        ).fetchall()

    scores = [dict(saved_score) for saved_score in saved_scores]
    return render_template(
        "leaderboard.html",
        scores=scores,
        difficulty_filters=DIFFICULTY_FILTERS,
        category_filters=CATEGORY_FILTERS,
        active_difficulty=active_difficulty,
        active_category=active_category
    )


@app.route("/review")
def review():
    answer_history = session.get("answer_history", [])
    if not answer_history:
        if session.get("selected_questions"):
            return redirect(url_for("result"))
        return redirect(url_for("home"))

    return render_template("review.html", answers=answer_history)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)
