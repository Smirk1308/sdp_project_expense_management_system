"""Simple rules for data received by the API."""

from typing import Literal

from pydantic import BaseModel, Field


class EntryInput(BaseModel):
    """Fields shared by an income entry and an expense entry."""

    user_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=80)
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=30)
    entry_date: str = Field(min_length=10, max_length=10)
    note: str = Field(default="", max_length=200)


class UserInput(BaseModel):
    """The name for a local user profile."""

    name: str = Field(min_length=1, max_length=40)


class CategoryInput(BaseModel):
    """The name and purpose of a category."""

    name: str = Field(min_length=1, max_length=30)
    type: Literal["income", "expense"]
