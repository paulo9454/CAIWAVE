from backend.services.demo.demo_mode import is_demo

class DemoMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, request, call_next):
        response = await call_next(request)

        if is_demo():
            response.headers["X-CAIWAVE-MODE"] = "DEMO"

        return response
