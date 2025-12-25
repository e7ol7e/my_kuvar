from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import Task

app = FastAPI()

# Создаём таблицы при старте
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Статические файлы (для HTMX, если добавите свои стили)
# app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session = Depends(get_session)):
    statement = select(Task).order_by(Task.created_at.desc())
    tasks = session.exec(statement).all()
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks})

@app.get("/tasks", response_class=HTMLResponse)
async def get_tasks(request: Request, session: Session = Depends(get_session)):
    statement = select(Task).order_by(Task.created_at.desc())
    tasks = session.exec(statement).all()
    return templates.TemplateResponse("partials/task_list.html", {"request": request, "tasks": tasks})

@app.post("/tasks", response_class=HTMLResponse)
async def create_task(
    request: Request,
    title: str = Form(...),
    description: str | None = Form(None),
    session: Session = Depends(get_session)
):
    task = Task(title=title, description=description)
    session.add(task)
    session.commit()
    session.refresh(task)

    statement = select(Task).order_by(Task.created_at.desc())
    tasks = session.exec(statement).all()
    return templates.TemplateResponse("partials/task_list.html", {"request": request, "tasks": tasks})

@app.patch("/tasks/{task_id}/toggle", response_class=HTMLResponse)
async def toggle_task(task_id: int, request: Request, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404)
    
    task.completed = not task.completed
    session.add(task)
    session.commit()

    tasks = session.exec(select(Task).order_by(Task.created_at.desc())).all()
    
    # Основной контент
    list_html = templates.TemplateResponse("partials/task_list.html", {"request": request, "tasks": tasks})
    
    # Добавляем OOB-своп для переинициализации HTMX
    oob_script = '<script src="https://unpkg.com/htmx.org@1.9.10" hx-oob-swap="true"></script>'
    
    return HTMLResponse(content=list_html.body + oob_script.encode())


@app.delete("/tasks/{task_id}", response_class=HTMLResponse)
async def delete_task(
    task_id: int,
    request: Request,
    session: Session = Depends(get_session)
):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    session.delete(task)
    session.commit()

    statement = select(Task).order_by(Task.created_at.desc())
    tasks = session.exec(statement).all()
    return templates.TemplateResponse("partials/task_list.html", {"request": request, "tasks": tasks})