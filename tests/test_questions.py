from questions import questions


def test_all_questions_have_required_fields():
    for index, question in enumerate(questions, start=1):
        assert question.get("question"), f"Question {index} is missing question text"
        assert question.get("choices"), f"Question {index} is missing choices"
        assert question.get("answer"), f"Question {index} is missing an answer"


def test_all_answers_are_in_choices():
    for index, question in enumerate(questions, start=1):
        assert question["answer"] in question["choices"], (
            f"Question {index} answer is not included in its choices: "
            f"{question['answer']}"
        )


def test_all_questions_have_four_unique_choices():
    for index, question in enumerate(questions, start=1):
        assert len(question["choices"]) == 4, (
            f"Question {index} should have exactly 4 choices"
        )
        assert len(question["choices"]) == len(set(question["choices"])), (
            f"Question {index} has duplicate choices"
        )


def test_question_text_is_unique():
    question_texts = [question["question"] for question in questions]
    assert len(question_texts) == len(set(question_texts))
