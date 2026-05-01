from __future__ import annotations

import reflex as rx
from reflex_local_auth.login import LoginState


class AuthState(LoginState):
    @rx.var(cache=True)
    def user_id(self) -> str:
        user = self.authenticated_user
        if user.id is not None and user.id >= 0:
            return str(user.username)
        return ""
