from pydantic import BaseModel


class TagDB(BaseModel):
    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True
