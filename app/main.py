from fastapi import FastAPI
from app.api import auth, documents
from app.core.logging_config import setup_logging

app = FastAPI(
    title="RagAPI",
    description="RagAPI",
    version="1.0",
)


all_routers = [
    auth.router,
    documents.router
]
setup_logging()

for router in all_routers:
    app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}



