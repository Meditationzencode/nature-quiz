import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session

load_dotenv()
try:
    from questions import questions, birds, trees, insects, animals
except Exception:
    questions = birds = trees = insects = animals = []
import random

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-fallback")

QUESTIONS_PER_GAME = 10


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start", methods=["GET", "POST"])
def start_quiz():
    if request.method == "POST":
        category = request.form.get("category", "All")
        pool = {"Birds": birds, "Trees": trees, "Insects": insects, "Animals": animals}.get(category, questions)

        if not pool:
            return render_template("500.html"), 500

        selected_questions = random.sample(pool, min(QUESTIONS_PER_GAME, len(pool)))

        session["selected_questions"] = selected_questions
        session["current_question"] = 0
        session["score"] = 0
        session["feedback"] = None

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
        feedback=feedback
    )


@app.route("/answer", methods=["POST"])
def answer():
    selected_questions = session.get("selected_questions")
    current_question = session.get("current_question", 0)

    if not selected_questions:
        return redirect(url_for("home"))

    if current_question >= len(selected_questions):
        return redirect(url_for("result"))

    chosen_answer = request.form.get("answer")
    if not chosen_answer:
        return redirect(url_for("quiz"))

    correct_answer = selected_questions[current_question]["answer"]

    is_correct = chosen_answer == correct_answer

    if is_correct:
        session["score"] = session.get("score", 0) + 1

    session["feedback"] = {
        "selected": chosen_answer,
        "correct": correct_answer,
        "is_correct": is_correct
    }

    return redirect(url_for("quiz"))


@app.route("/next", methods=["POST"])
def next_question():
    if not session.get("selected_questions"):
        return redirect(url_for("home"))

    current_question = session.get("current_question", 0)
    session["current_question"] = current_question + 1
    session["feedback"] = None

    return redirect(url_for("quiz"))


@app.route("/timeout", methods=["POST"])
def timeout():
    if not session.get("selected_questions"):
        return redirect(url_for("home"))

    current_question = session.get("current_question", 0)
    session["current_question"] = current_question + 1
    session["feedback"] = None

    return redirect(url_for("quiz"))


@app.route("/result")
def result():
    selected_questions = session.get("selected_questions", [])
    score = session.get("score", 0)
    total_questions = len(selected_questions)

    if total_questions == 0:
        return redirect(url_for("home"))

    percentage = round((score / total_questions) * 100)

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
        message=message
    )


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)