"""Take screenshots of every page in the quiz for the README."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from questions import questions

IMAGES = Path("static/images")
BASE = "http://127.0.0.1:5000"

# The quiz page ticks a countdown once a second, and each redraw nudges the
# layout by a fraction of a pixel. Freezing setInterval parks the timer at its
# starting value, which keeps the layout still and makes every screenshot show
# the same "60s" instead of an arbitrary point in the countdown. The countdown
# is the only interval on the page; main.js uses setTimeout.
FREEZE_TIMER = "window.setInterval = () => 0;"

answer_lookup = {q["question"]: q["answer"] for q in questions}


def start_server():
    return subprocess.Popen(
        [sys.executable, "-m", "waitress", "--port=5000", "app:app"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_for_server(page):
    for _ in range(20):
        try:
            page.goto(BASE, timeout=2000)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Server did not start")


def answer_selector(answer):
    """Build a button selector for an answer, which may contain quotes."""
    escaped = answer.replace("\\", "\\\\").replace('"', '\\"')
    return f'button[value="{escaped}"]'


def click(page, selector):
    """Click, with the cursor parked off the controls first.

    .answer-button lifts itself 2px on :hover. If the cursor happens to be
    left sitting on a button's edge after the previous click, that lift moves
    the button out from under the cursor, which un-hovers it, which drops it
    back — an oscillation Playwright waits out until it times out. Parking the
    mouse in the corner first means nothing is hovered when it measures.
    """
    page.mouse.move(0, 0)
    page.click(selector)


def shot(page, name, wait_ms=400, full_page=False):
    page.wait_for_timeout(wait_ms)
    page.screenshot(path=str(IMAGES / name), full_page=full_page)
    print(f"  saved {name}")


def play_quiz(page, difficulty="Easy", category="All", answers_to_take=10):
    page.goto(BASE + "/start")
    click(page, f"button[value='{difficulty}']")
    page.wait_for_url("**/category")
    click(page, f"button[value='{category}']")
    page.wait_for_url("**/quiz")

    for i in range(answers_to_take):
        page.wait_for_selector(".question-text")
        q_text = page.inner_text(".question-text")
        answer = answer_lookup.get(q_text.strip())

        if i == 0 and difficulty == "Easy":
            shot(page, "screenshot-quiz.png")

        if answer:
            click(page, answer_selector(answer))
        else:
            click(page, ".answer-button")

        page.wait_for_selector(".feedback-box")

        if i == 0 and difficulty == "Easy":
            shot(page, "screenshot-feedback.png")

        click(page, "button[type='submit']")
        page.wait_for_timeout(200)

        if "/result" in page.url:
            break


def main():
    server = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()

            # --- Desktop screenshots ---
            page = browser.new_page(viewport={"width": 900, "height": 700})
            page.add_init_script(FREEZE_TIMER)
            wait_for_server(page)

            # Home — full page so the footer (source-code link) is visible
            page.goto(BASE)
            shot(page, "screenshot-home.png", full_page=True)

            # Difficulty (now shows points per answer)
            page.goto(BASE + "/start")
            shot(page, "screenshot-difficulty.png")

            # Category (need difficulty in session first)
            click(page, "button[value='Easy']")
            page.wait_for_url("**/category")
            shot(page, "screenshot-category.png")

            # Play a full Easy/All game — captures quiz, feedback, streak
            play_quiz(page, difficulty="Easy", category="All")

            # Streak (play hard enough to get 2 in a row)
            # Re-play and capture streak badge if visible
            page.goto(BASE + "/start")
            click(page, "button[value='Medium']")
            page.wait_for_url("**/category")
            click(page, "button[value='All']")
            page.wait_for_url("**/quiz")

            correct_count = 0
            for _ in range(10):
                page.wait_for_selector(".question-text")
                q_text = page.inner_text(".question-text")
                answer = answer_lookup.get(q_text.strip())

                if answer:
                    click(page, answer_selector(answer))
                    correct_count += 1
                else:
                    click(page, ".answer-button")

                page.wait_for_selector(".feedback-box")
                click(page, "button[type='submit']")
                page.wait_for_timeout(200)

                if "/result" in page.url:
                    break

                # Capture streak badge if it appears
                if correct_count >= 2 and page.query_selector(".streak"):
                    shot(page, "screenshot-streak.png")

            # Results page
            if "/result" in page.url:
                shot(page, "screenshot-results.png")

                # Review answers page (new)
                click(page, "a[href*='review']")
                page.wait_for_url("**/review")
                shot(page, "screenshot-review.png")

                # Back to results then leaderboard
                click(page, "a[href*='result']")
                page.wait_for_url("**/result")

            # Leaderboard (with filters)
            page.goto(BASE + "/leaderboard")
            shot(page, "screenshot-leaderboard.png")

            # Leaderboard filtered view
            click(page, "a.filter-button[href*='difficulty=Hard']")
            page.wait_for_timeout(300)
            shot(page, "screenshot-leaderboard-filtered.png")

            # --- Mobile screenshot ---
            mobile = browser.new_page(viewport={"width": 390, "height": 844})
            mobile.add_init_script(FREEZE_TIMER)
            mobile.goto(BASE)
            shot(mobile, "screenshot-mobile.png")

            browser.close()
    finally:
        server.terminate()

    print("\nDone.")


if __name__ == "__main__":
    main()
