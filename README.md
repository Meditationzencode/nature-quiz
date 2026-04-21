# Nature Quiz

A polished quiz web app built with **Python** and **Flask** that tests users on their knowledge of the natural world. Each game selects **10 random questions** from a bank of **50 nature questions**, making the quiz replayable and varied.

## Overview

This project was built to practice core web development concepts with Flask, including routing, templates, session-based state management, and dynamic quiz logic. It also includes a countdown timer and a responsive, nature-themed interface designed to create a more engaging user experience.

## Features

- Flask-based web application
- 50 nature-themed multiple-choice questions
- 10 random questions per game
- Score tracking across a quiz session
- Instant answer feedback
- Final score and percentage results
- Countdown timer for each question
- Play Again flow for replayability
- Responsive layout for desktop and smaller screens
- Nature-themed visual design

## Tech Stack

- Python
- Flask
- HTML
- CSS
- JavaScript

## Project Structure

```text
nature-quiz/
├─ app.py
├─ questions.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ static/
│  ├─ style.css
│  └─ images/
└─ templates/
   ├─ layout.html
   ├─ index.html
   ├─ quiz.html
   └─ result.html
```

## How It Works

1. The user starts the quiz from the home page.
2. The application randomly selects 10 questions from the full question bank.
3. One question is shown at a time.
4. The user selects an answer before the timer runs out.
5. The app provides answer feedback and updates the score.
6. After the final question, the results page displays the total score and percentage.

## Installation

### Clone the repository

```bash
git clone https://github.com/Meditationzencode/nature-quiz.git
cd nature-quiz
```

### Create and activate a virtual environment

**Windows**
```bash
py -3 -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install Flask
```

Or, if using `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
python -m flask --app app run --debug
```

Then open:

```text
http://127.0.0.1:5000
```

## Example Questions

- Which animal is famous for carrying its home on its back?
- What do bees collect from flowers?
- Which bird cannot fly?
- What do caterpillars turn into?
- Which of these animals is the largest?

## Screenshots

![Home Page](static/images/homepage-screenshot.png)
![Quiz Page](static/images/quiz-screenshot.png)
![Results Page](static/images/results-screenshot.png)

## Skills Demonstrated

This project highlights:

- Python application development
- Flask routing and template rendering
- Session management
- Working with structured quiz data
- Frontend integration with HTML, CSS, and JavaScript
- Basic UI/UX design for an interactive web app

## Author

**Bradley**

GitHub: [https://github.com/Meditationzencode](https://github.com/Meditationzencode)
