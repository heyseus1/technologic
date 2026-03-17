from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from hue_async.core.config import get_settings
from hue_async.web.deps import get_room_service


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

settings = get_settings()

app = FastAPI(title="Hue Control Portal")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.WEB_SESSION_SECRET,
    same_site="lax",
    https_only=False,  # local-only for now
)


def require_user(request: Request) -> str:
    username = request.session.get("user")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return username


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None,
            "user": None,
        },
    )


@app.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username != settings.WEB_USERNAME or password != settings.WEB_PASSWORD:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid credentials",
                "user": None,
            },
            status_code=401,
        )

    request.session["user"] = username
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    username: str = Depends(require_user),
):
    service = get_room_service()
    rooms = service.list_rooms()

    room_states = []
    for room in rooms:
        is_on, bri = service.get_grouped_light_state(room.grouped_light_id)
        room_states.append(
            {
                "room": room,
                "is_on": is_on,
                "brightness": bri,
            }
        )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": username,
            "room_states": room_states,
        },
    )


@app.get("/rooms/{room_id}", response_class=HTMLResponse)
def room_detail(
    room_id: str,
    request: Request,
    username: str = Depends(require_user),
):
    service = get_room_service()
    rooms = service.list_rooms()

    room = next((r for r in rooms if r.room_id == room_id), None)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    is_on, bri = service.get_grouped_light_state(room.grouped_light_id)
    scenes = service.list_scenes_for_room(room.room_id)

    return templates.TemplateResponse(
        "room.html",
        {
            "request": request,
            "user": username,
            "room": room,
            "is_on": is_on,
            "brightness": bri,
            "scenes": scenes,
        },
    )


@app.post("/rooms/{room_id}/power")
def set_power(
    room_id: str,
    request: Request,
    power: str = Form(...),
    username: str = Depends(require_user),
):
    service = get_room_service()
    rooms = service.list_rooms()

    room = next((r for r in rooms if r.room_id == room_id), None)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    target = power.lower() == "on"
    service.set_room_power(room.grouped_light_id, target)

    return RedirectResponse(url=f"/rooms/{room_id}", status_code=303)


@app.post("/rooms/{room_id}/scene")
def activate_scene(
    room_id: str,
    request: Request,
    scene_id: str = Form(...),
    username: str = Depends(require_user),
):
    service = get_room_service()
    rooms = service.list_rooms()

    room = next((r for r in rooms if r.room_id == room_id), None)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    service.activate_scene(scene_id)

    return RedirectResponse(url=f"/rooms/{room_id}", status_code=303)


@app.post("/rooms/{room_id}/brightness")
def set_brightness(
    room_id: str,
    request: Request,
    brightness: float = Form(...),
    username: str = Depends(require_user),
):
    service = get_room_service()
    rooms = service.list_rooms()

    room = next((r for r in rooms if r.room_id == room_id), None)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    brightness = max(0.0, min(100.0, brightness))
    service.set_room_brightness(room.grouped_light_id, brightness)

    return RedirectResponse(url=f"/rooms/{room_id}", status_code=303)