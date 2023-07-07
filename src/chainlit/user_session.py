from typing import Dict
from chainlit.context import get_emitter

user_sessions: Dict[str, Dict] = {}


class UserSession:
    """
    Developer facing user session class.
    Useful for the developer to store user specific data between calls.
    """

    def get(self, key):
        emitter = get_emitter()
        if not emitter:
            return None

        if emitter.session["id"] not in user_sessions:
            # Create a new user session
            user_sessions[emitter.session["id"]] = {}

        user_session = user_sessions[emitter.session["id"]]

        # Copy important fields from the session
        user_session["id"] = emitter.session["id"]
        user_session["env"] = emitter.session["user_env"]

        return user_session.get(key)

    def set(self, key, value):
        emitter = get_emitter()
        if not emitter:
            return None

        if emitter.session["id"] not in user_sessions:
            user_sessions[emitter.session["id"]] = {}

        user_session = user_sessions[emitter.session["id"]]
        user_session[key] = value


user_session = UserSession()
