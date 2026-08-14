import pytest
from app import CATEGORIES, DIFFICULTY_TIMERS, QUESTIONS_PER_GAME, pool_for
from questions import questions, birds, trees, insects, animals

ALL_LISTS = [
    ("questions", questions),
    ("birds", birds),
    ("trees", trees),
    ("insects", insects),
    ("animals", animals),
]


@pytest.mark.parametrize("name,pool", ALL_LISTS)
def test_all_questions_have_required_fields(name, pool):
    for index, question in enumerate(pool, start=1):
        assert question.get("question"), f"{name}[{index}] is missing question text"
        assert question.get("choices"), f"{name}[{index}] is missing choices"
        assert question.get("answer"), f"{name}[{index}] is missing an answer"


@pytest.mark.parametrize("name,pool", ALL_LISTS)
def test_all_answers_are_in_choices(name, pool):
    for index, question in enumerate(pool, start=1):
        assert question["answer"] in question["choices"], (
            f"{name}[{index}] answer not in choices: {question['answer']}"
        )


@pytest.mark.parametrize("name,pool", ALL_LISTS)
def test_all_questions_have_four_unique_choices(name, pool):
    for index, question in enumerate(pool, start=1):
        assert len(question["choices"]) == 4, (
            f"{name}[{index}] should have exactly 4 choices"
        )
        assert len(question["choices"]) == len(set(question["choices"])), (
            f"{name}[{index}] has duplicate choices"
        )


def test_question_text_is_unique():
    question_texts = [question["question"] for question in questions]
    assert len(question_texts) == len(set(question_texts))


@pytest.mark.parametrize("name,pool", ALL_LISTS)
def test_all_questions_have_a_valid_difficulty(name, pool):
    for index, question in enumerate(pool, start=1):
        assert question.get("difficulty") in DIFFICULTY_TIMERS, (
            f"{name}[{index}] has difficulty {question.get('difficulty')!r}, "
            f"expected one of {list(DIFFICULTY_TIMERS)}"
        )


@pytest.mark.parametrize("category", list(CATEGORIES))
@pytest.mark.parametrize("difficulty", list(DIFFICULTY_TIMERS))
def test_every_pool_can_fill_a_game(category, difficulty):
    """Every difficulty/category pairing must yield a full game, whether from
    its own questions or by falling back to a neighbouring difficulty."""
    pool = pool_for(category, difficulty)
    assert len(pool) >= QUESTIONS_PER_GAME, (
        f"{category}/{difficulty} can only field {len(pool)} questions"
    )
