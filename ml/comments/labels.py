from enum import StrEnum


class CommentLabel(StrEnum):
    """The 6 classes from docs/label-guideline.md and FR-7.2."""

    QUESTION = "question"
    REQUEST = "request"
    PRAISE = "praise"
    OBJECTION = "objection"
    COMPLAINT = "complaint"
    SPAM = "spam"
