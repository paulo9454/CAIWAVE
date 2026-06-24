from backend.core.demo_mode import DEMO_MODE
from fastapi import Request

class DemoMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")

            # allow everything, just tag request
            scope["state"] = {"demo_mode": DEMO_MODE}

        await self.app(scope, receive, send)
