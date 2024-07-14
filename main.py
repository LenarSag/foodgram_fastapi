import asyncio

import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import ValidationException

from db.database import init_models
from api.login import loginrouter
from api.users import usersrouter
from api.ingredients import ingredientsrouter
from api.tags import tagsrouter
from api.recipes import recipesrouter
from api.short_url import shorturlrouter


API_URL = "api"

app = FastAPI()

app.include_router(loginrouter, prefix=f"/{API_URL}/auth/token")
app.include_router(usersrouter, prefix=f"/{API_URL}/users")
app.include_router(ingredientsrouter, prefix=f"/{API_URL}/ingredients")
app.include_router(tagsrouter, prefix=f"/{API_URL}/tags")
app.include_router(recipesrouter, prefix=f"/{API_URL}/recipes")
app.include_router(shorturlrouter, prefix="/s")


@app.exception_handler(ValidationException)
async def custom_pydantic_validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()}
    )


@app.get("/")
async def index():
    return "Foodgram Fastapi"


if __name__ == "__main__":
    asyncio.run(init_models())
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)
