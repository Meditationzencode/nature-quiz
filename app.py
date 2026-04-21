from flask import Flask, render_template, request, redirect, url_for, session
from questions import questions
import random

app = Flask(__name__)
app.secret_key = "change-this-to-a-secret-key"

QUESTIONS_PER_GAME = 10


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start")
def start_quiz():
    selected_questions = random.sample(
        questions,
        min(QUESTIONS_PER_GAME, len(questions))
    )

    session["selected_questions"] = selected_questions
    session["current_question"] = 0
    session["score"] = 0
    session["feedback"] = None

    return redirect(url_for("quiz"))


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


if __name__ == "__main__":
    app.run(debug=True)