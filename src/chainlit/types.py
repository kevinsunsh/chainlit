from typing import List, Any, TypedDict, Optional, Literal, Dict, Union
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from dataclasses_json import dataclass_json

ElementType = Literal["image", "avatar", "text", "pdf", "tasklist"]
ElementDisplay = Literal["inline", "side", "page"]
ElementSize = Literal["small", "medium", "large"]


@dataclass_json
@dataclass
class AskSpec:
    """Specification for asking the user."""

    timeout: int
    type: Literal["text", "file"]


@dataclass_json
@dataclass
class AskFileSpec(AskSpec):
    """Specification for asking the user for a file."""

    accept: Union[List[str], Dict[str, List[str]]]
    max_files: int
    max_size_mb: int


class AskResponse(TypedDict):
    content: str
    author: str


@dataclass
class AskFileResponse:
    name: str
    path: str
    size: int
    type: str
    content: bytes


class CompletionRequest(BaseModel):
    prompt: str
    userEnv: Dict[str, str]


class UpdateFeedbackRequest(BaseModel):
    messageId: int
    feedback: int


class DeleteConversationRequest(BaseModel):
    conversationId: int


class Pagination(BaseModel):
    first: int
    cursor: Any


class ConversationFilter(BaseModel):
    feedback: Optional[Literal[-1, 0, 1]]
    authorEmail: Optional[str]
    search: Optional[str]


class GetConversationsRequest(BaseModel):
    pagination: Pagination
    filter: ConversationFilter
