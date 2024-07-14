from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from utils.short_url import get_decoded_short_url


shorturlrouter = APIRouter()


@shorturlrouter.get("/{short_url}")
async def handle_short_url(
    request: Request,
    short_url: str
):
    try:
        decoded_values = get_decoded_short_url(short_url)
        if decoded_values:
            recipe_id = decoded_values[0]
            return RedirectResponse(
                url=f"{str(request.url.scheme)}://{str(request.url.netloc)}"
                    f"/api/recipes/{recipe_id}/")
        return HTTPException(
            detail="URL-адрес недействителен или срок его действия истек.",
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return HTTPException(
            detail=f"Произошла ошибка {e} при обработке URL-адреса.",
            status_code=status.HTTP_404_NOT_FOUND
        )
