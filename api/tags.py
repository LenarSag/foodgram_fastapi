from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crud.tag_repository import get_all_tags, get_tag_by_id
from db.database import get_session
from schemas.tag_schema import TagDB


tagsrouter = APIRouter()


@tagsrouter.get("/", response_model=list[TagDB])
async def get_tags(session: AsyncSession = Depends(get_session)):
    tags = await get_all_tags(session)
    return tags


@tagsrouter.get("/{tag_id}", response_model=TagDB)
async def get_tag(
    tag_id: int, session: AsyncSession = Depends(get_session)
):
    tag = await get_tag_by_id(session, tag_id)
    if not tag:
        raise HTTPException(
            detail="Tag not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return tag
