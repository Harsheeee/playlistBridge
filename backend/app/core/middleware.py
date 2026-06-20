from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Scope, Receive, Send

class XForwardedHostMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        if b"x-forwarded-host" in headers:
            forwarded_host = headers[b"x-forwarded-host"].decode("latin1")
            
            # Handle host:port
            if ":" in forwarded_host:
                host, port_str = forwarded_host.split(":", 1)
                port = int(port_str)
            else:
                host = forwarded_host
                # Default ports based on scheme
                scheme = scope.get("scheme", "http")
                if b"x-forwarded-proto" in headers:
                    scheme = headers[b"x-forwarded-proto"].decode("latin1").split(",")[0].strip()
                port = 443 if scheme == "https" else 80

            # Update the scope's server and headers
            scope["server"] = (host, port)
            
            # Update the host header so request.url and request.base_url use it
            new_headers = []
            for k, v in scope["headers"]:
                if k == b"host":
                    new_headers.append((b"host", forwarded_host.encode("latin1")))
                else:
                    new_headers.append((k, v))
            scope["headers"] = new_headers

        await self.app(scope, receive, send)
