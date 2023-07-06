from dotenv import load_dotenv
from typing import Callable, Any, TYPE_CHECKING
import os
import asyncio

if TYPE_CHECKING:
    from chainlit.backend.base import BaseBackend

from chainlit.utils import wrap_user_function
from chainlit.config import config
from chainlit.telemetry import trace
from chainlit.version import __version__
from chainlit.logger import logger
from chainlit.action import Action
from chainlit.element import (
    Image,
    Text,
    Pdf,
    Avatar,
    Pyplot,
    TaskList,
    Task,
    TaskStatus,
)
from chainlit.message import Message, ErrorMessage, AskUserMessage, AskFileMessage
from chainlit.user_session import user_session
from chainlit.sync import run_sync, make_async

env_found = load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

if env_found:
    logger.info("Loaded .env file")


@trace
def on_message(func: Callable) -> Callable:
    """
    Framework agnostic decorator to react to messages coming from the UI.
    The decorated function is called every time a new message is received.

    Args:
        func (Callable[[str], Any]): The function to be called when a new message is received. Takes the input message.

    Returns:
        Callable[[str], Any]: The decorated on_message function.
    """

    config.code.on_message = wrap_user_function(func)
    return func


@trace
def on_chat_start(func: Callable) -> Callable:
    """
    Hook to react to the user websocket connection event.

    Args:
        func (Callable[], Any]): The connection hook to execute.

    Returns:
        Callable[], Any]: The decorated hook.
    """

    config.code.on_chat_start = wrap_user_function(func, with_task=True)
    return func


@trace
def on_stop(func: Callable) -> Callable:
    """
    Hook to react to the user stopping a conversation.

    Args:
        func (Callable[[], Any]): The stop hook to execute.

    Returns:
        Callable[[], Any]: The decorated stop hook.
    """

    config.code.on_stop = wrap_user_function(func)
    return func


def action_callback(name: str) -> Callable:
    """
    Callback to call when an action is clicked in the UI.

    Args:
        func (Callable[[Action], Any]): The action callback to execute. First parameter is the action.
    """

    def decorator(func: Callable[[Action], Any]):
        config.code.action_callbacks[name] = wrap_user_function(func, with_task=True)
        return func

    return decorator


def sleep(duration: int):
    """
    Sleep for a given duration.
    Args:
        duration (int): The duration in seconds.
    """
    return asyncio.sleep(duration)


__all__ = [
    "user_session",
    "Action",
    "Pdf",
    "Image",
    "Text",
    "Avatar",
    "Pyplot",
    "Task",
    "TaskList",
    "TaskStatus",
    "Message",
    "ErrorMessage",
    "AskUserMessage",
    "AskFileMessage",
    "on_chat_start",
    "on_stop",
    "action_callback",
    "sleep",
    "run_sync",
    "make_async",
]
