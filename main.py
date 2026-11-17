from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app import models  


from app.controllers import auth, projects, boards, columns, cards, comments

# Создаем таблицы БД (если ещё их нет)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kanban API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(boards.router, prefix="/boards", tags=["Boards"])
app.include_router(columns.router, prefix="/columns", tags=["Columns"])
app.include_router(cards.router, prefix="/cards", tags=["Cards"])
app.include_router(comments.router, prefix="/comments", tags=["Comments"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Kanban API работает"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)