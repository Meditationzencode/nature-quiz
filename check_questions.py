"""Report progress and catch mistakes while writing new questions.

Run it any time:  python check_questions.py

Deliberately imports nothing but questions.py, so it works without Flask or
pytest installed. Exits non-zero if it finds a problem.
"""
import sys
import questions as bank

TARGET = 25
CATEGORIES = ["birds", "trees", "insects", "animals"]
DIFFICULTIES = ["easy", "medium", "hard"]


def problems_in(name, pool):
    seen = set()
    for index, question in enumerate(pool, start=1):
        where = f"{name}[{index}]"
        text = question.get("question")
        choices = question.get("choices")
        answer = question.get("answer")

        if not text:
            yield f"{where} has no question text"
            continue
        if not choices:
            yield f"{where} has no choices"
            continue
        if len(choices) != 4:
            yield f"{where} has {len(choices)} choices, needs exactly 4"
        if len(set(choices)) != len(choices):
            yield f"{where} has duplicate choices"
        if not answer:
            yield f"{where} has no answer"
        elif answer not in choices:
            yield f"{where} answer {answer!r} is not one of its choices"
        if text in seen:
            yield f"{where} duplicates an earlier question in the same list"
        seen.add(text)


def main():
    rows = []
    found = []

    for category in CATEGORIES:
        counts = {}
        for difficulty in DIFFICULTIES:
            name = f"{category}_{difficulty}"
            pool = getattr(bank, name, [])
            counts[difficulty] = len(pool)
            found.extend(problems_in(name, pool))
        rows.append((category, counts))

    width = 54
    print(f"{'Category':<10}{'Easy':>6}{'Medium':>19}{'Hard':>19}")
    print("-" * width)
    for category, counts in rows:
        cells = []
        for difficulty in ("medium", "hard"):
            n = counts[difficulty]
            mark = "done" if n >= TARGET else f"{TARGET - n} to go"
            cells.append(f"{n}/{TARGET} ({mark})")
        print(f"{category:<10}{counts['easy']:>6}{cells[0]:>19}{cells[1]:>19}")

    total_new = sum(c["medium"] + c["hard"] for _, c in rows)
    print("-" * width)
    print(f"new questions written: {total_new} / {TARGET * len(CATEGORIES) * 2}")

    duplicates = duplicate_text_across_bank()
    found.extend(duplicates)

    print()
    if found:
        print(f"{len(found)} problem(s) to fix:")
        for problem in found:
            print(f"  - {problem}")
        return 1

    print("no problems found")
    return 0


def duplicate_text_across_bank():
    seen = {}
    for category in CATEGORIES:
        for difficulty in DIFFICULTIES:
            name = f"{category}_{difficulty}"
            for question in getattr(bank, name, []):
                text = question.get("question")
                if not text:
                    continue
                if text in seen and seen[text] != name:
                    yield f"{name} repeats a question already in {seen[text]}: {text!r}"
                seen[text] = name


if __name__ == "__main__":
    sys.exit(main())
