from typing import Optional

from fastapi import Request


def get_prev_and_next_page(
    request: Request, page: int, size: int, total: int
) -> tuple[Optional[str], Optional[str]]:
    base_url = str(request.url).split("?")[0]
    next_url = (
        f"{base_url}?page={page + 1}&size={size}"
        if (page * size) < total else None
    )
    previous_url = (
        f"{base_url}?page={page - 1}&size={size}"
        if page > 1 else None
    )
    return next_url, previous_url
