from fastapi import FastAPI
from starlette.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.middleware import APIKeyMiddleware, setup_middleware

class DummySettings:

    def __init__(self, **kwargs):
        self.enable_api_key_auth = kwargs.get('enable_api_key_auth', True)
        self.api_key_header = kwargs.get('api_key_header', 'x-api-key')
        self.api_keys = kwargs.get('api_keys', ['valid-key'])
        self.exclude_api_key_paths = kwargs.get('exclude_api_key_paths', ['/docs'])
        self.debug = kwargs.get('debug', False)

def app_with_middleware():
    app = FastAPI()
    setup_middleware(app)
    return app

class TestAPIKeyMiddleware:

    def make_request(self, app, path="/", headers=None, client_host="1.2.3.4",
                    user_agent="test-agent", referer=None):
        client = TestClient(app)
        extra = {}
        if headers:
            extra['headers'] = headers
        if referer:
            if 'headers' not in extra:
                extra['headers'] = {}
            extra['headers']['referer'] = referer
        # Patch request.client.host
        with patch("starlette.requests.Request.client",
                  new_callable=MagicMock(return_value=MagicMock(host=client_host))):
            return client.get(path, **extra)

    def test_api_key_disabled(self):
        app = FastAPI()
        app.add_middleware(APIKeyMiddleware, settings=DummySettings(enable_api_key_auth=False))

        @app.get("/")
        def root():
            return {"ok": True}
        response = self.make_request(app)
        assert response.status_code == 200

    def test_api_key_valid(self):
        app = FastAPI()
        app.add_middleware(APIKeyMiddleware, settings=DummySettings(api_keys=["valid-key"]))

        @app.get("/")
        def root():
            return {"ok": True}
        response = self.make_request(app, headers={"x-api-key": "valid-key"})
        assert response.status_code == 200

    def test_api_key_invalid(self):
        app = FastAPI()
        app.add_middleware(APIKeyMiddleware, settings=DummySettings(api_keys=["valid-key"]))

        @app.get("/")
        def root():
            return {"ok": True}
        response = self.make_request(app, headers={"x-api-key": "invalid-key"})
        assert response.status_code == 401
        assert "Invalid API key" in response.text

    def test_api_key_missing(self):
        app = FastAPI()
        app.add_middleware(APIKeyMiddleware, settings=DummySettings(api_keys=["valid-key"]))

        @app.get("/")
        def root():
            return {"ok": True}
        response = self.make_request(app)
        assert response.status_code == 401
        assert "API key required" in response.text

    def test_api_key_skip_exclude_path(self):
        app = FastAPI()
        app.add_middleware(APIKeyMiddleware, settings=DummySettings(exclude_api_key_paths=["/docs"]))

        @app.get("/docs")
        def docs():
            return {"ok": True}
        response = self.make_request(app, path="/docs")
        assert response.status_code == 200

    def test_api_key_skip_user_agent(self):
        app = FastAPI()
        app.add_middleware(APIKeyMiddleware, settings=DummySettings())

        @app.get("/")
        def root():
            return {"ok": True}
        # User agent contains 'swagger'
        response = self.make_request(app, headers={"user-agent": "swagger-ui"})
        assert response.status_code == 200

    def test_api_key_skip_referer(self):
        app = FastAPI()
        app.add_middleware(APIKeyMiddleware, settings=DummySettings())

        @app.get("/")
        def root():
            return {"ok": True}
        response = self.make_request(app, referer="/docs")
        assert response.status_code == 200

    def test_api_key_skip_debug(self):
        app = FastAPI()
        app.add_middleware(APIKeyMiddleware, settings=DummySettings(debug=True))

        @app.get("/")
        def root():
            return {"ok": True}
        response = self.make_request(app)
        assert response.status_code == 200

    def test_api_key_skip_localhost(self):
        app = FastAPI()
        app.add_middleware(APIKeyMiddleware, settings=DummySettings())

        @app.get("/")
        def root():
            return {"ok": True}
        response = self.make_request(app, client_host="127.0.0.1")
        assert response.status_code == 200

class TestSetupMiddleware:

    def test_setup_middleware_adds_all(self):
        app = FastAPI()
        setup_middleware(app)
        # Check that all middleware classes are present
        middleware_classes = [mw.cls for mw in app.user_middleware]
