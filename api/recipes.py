from typing import Optional

from fastapi import (
    APIRouter, HTTPException, Query, Depends, Request, Response, status
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession


recipesrouter = APIRouter()

@recipesrouter.get("/")
async def get_recipes(session: AsyncSession):
    pass