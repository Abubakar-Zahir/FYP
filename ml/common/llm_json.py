"""Shared handling of JSON answers from an LLM: fences, validation, and a readable problem."""

import json

from pydantic import BaseModel, ValidationError


class LlmAnswerError(Exception):
    """The answer could not be read. The message says why, so it can go back to the model."""


def strip_code_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


def parse_json_answer[Model: BaseModel](raw: str, model: type[Model]) -> Model:
    try:
        return model.model_validate(json.loads(strip_code_fence(raw)))
    except json.JSONDecodeError as error:
        raise LlmAnswerError("The answer was not valid JSON.") from error
    except ValidationError as error:
        problems = "; ".join(f"{'.'.join(map(str, item['loc']))}: {item['msg']}" for item in error.errors())
        raise LlmAnswerError(f"The JSON did not match the format: {problems}") from error
