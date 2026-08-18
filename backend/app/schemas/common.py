"""Shared schema building blocks."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field

Locale = Literal["fr", "en"]


class ApiModel(BaseModel):
    """Base model: reads ORM attributes and forbids unknown input fields."""

    model_config = ConfigDict(from_attributes=True, extra="forbid", str_strip_whitespace=True)


class LocalizedString(ApiModel):
    """One string in both site locales.

    Sending both locales lets the language switcher work without a refetch,
    which keeps the public flyer snappy on a phone at the property gate.
    """

    fr: str
    en: str

    @classmethod
    def of(cls, fr: str, en: str) -> Self:
        """Build a localized string from its two values."""
        return cls(fr=fr, en=en)


class Message(ApiModel):
    """Simple acknowledgement payload."""

    detail: str


class Page[T](ApiModel):
    """A slice of a longer list."""

    items: list[T]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)
