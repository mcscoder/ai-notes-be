from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    message: str


class AiActionRequest(BaseModel):
    """
    Optional request body parameters for AI actions.
    """

    style: Optional[str] = None  # e.g., "professional", "casual" for /refine
    max_tokens: Optional[int] = None  # Approx word count for /continue
    max_length: Optional[int] = None  # Approx word count for /summarize
