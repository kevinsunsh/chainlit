from typing import Dict, TypedDict, Optional, Callable, Any, Union
from chainlit.backend.base import BaseBackend
from chainlit.types import AskResponse


class Session(TypedDict):
    """Internal session object."""

    # The ID of the session
    id: str
    # Function to ask the user a question
    ask_user: Callable[[Any, Optional[int]], Union[AskResponse, None]]
    # Function to emit a message to the user
    emit: Callable[[str, Any], None]
    # User specific environment variables. Empty if no user environment variables are required.
    user_env: Dict[str, str]
    # Whether the current task should be stopped
    should_stop: bool
    # Optional client to persist messages and files
    client: Optional[BaseBackend]


sessions: Dict[str, Session] = {}
