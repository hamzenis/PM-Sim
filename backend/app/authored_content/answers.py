"""Strict answer normalization.  Skipping is intentionally not an answer command."""

from __future__ import annotations

from typing import Any

from .constants import SHORT_TEXT_MAX_LENGTH


class AnswerError(ValueError):
    pass


def normalize_answer(question: Any, answer: Any, *, completed: bool = False) -> Any:
    if completed:
        raise AnswerError("question has already been completed")
    data = question.model_dump(mode="python") if hasattr(question, "model_dump") else question
    schema = data["answer_schema"]
    required = data.get("required", True)
    options = data.get("options", [])
    option_ids = [item.id if hasattr(item, "id") else item["id"] for item in options]

    if schema == "single_choice":
        if not isinstance(answer, str):
            raise AnswerError("single choice answer must be one option ID")
        if answer not in option_ids:
            raise AnswerError("unknown option ID")
        return answer
    if schema == "multiple_choice":
        if not isinstance(answer, list) or any(not isinstance(item, str) for item in answer):
            raise AnswerError("multiple choice answer must be an array of option IDs")
        if len(answer) != len(set(answer)):
            raise AnswerError("multiple choice answer contains duplicate option IDs")
        if not set(answer).issubset(option_ids):
            raise AnswerError("unknown option ID")
        if required and not answer:
            raise AnswerError("required answer cannot be empty")
        selected = set(answer)
        return [option_id for option_id in option_ids if option_id in selected]
    if schema == "boolean":
        if type(answer) is not bool:
            raise AnswerError("boolean answer must be a JSON boolean")
        return answer
    if schema == "short_text":
        if not isinstance(answer, str):
            raise AnswerError("short text answer must be a string")
        if required and answer == "":
            raise AnswerError("required answer cannot be empty")
        maximum = data.get("short_text_max_length") or SHORT_TEXT_MAX_LENGTH
        if len(answer) > maximum:
            raise AnswerError(f"short text answer exceeds {maximum} characters")
        return answer
    raise AnswerError(f"unsupported answer schema: {schema}")
