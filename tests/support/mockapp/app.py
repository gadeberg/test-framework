"""The framework's own FastAPI mock: a deterministic, offline target for the
contract tests that prove the shared step library actually drives a real
server (JSON API + rendered HTML), not just its own mocks.
"""

from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

VALID_EMAIL = "user@example.com"
VALID_PASSWORD = "correct-password"

app = FastAPI()


class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    token: str


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/whoami")
def whoami(authorization: str | None = Header(default=None)) -> dict[str, str | None]:
    return {"authorization": authorization}


@app.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if payload.email == VALID_EMAIL and payload.password == VALID_PASSWORD:
        return LoginResponse(token="fake-jwt-token")
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


LOGIN_PAGE_HTML = """<!doctype html>
<html>
<body>
  <input id="email" name="email" />
  <input id="password" name="password" type="password" />
  <button id="submit">Log in</button>
  <div id="error"></div>
  <script>
    document.getElementById('submit').addEventListener('click', async () => {
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      const resp = await fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password}),
      });
      const data = await resp.json();
      document.getElementById('error').textContent = data.error || '';
    });
  </script>
</body>
</html>"""


@app.get("/login-page", response_class=HTMLResponse)
def login_page() -> str:
    return LOGIN_PAGE_HTML
