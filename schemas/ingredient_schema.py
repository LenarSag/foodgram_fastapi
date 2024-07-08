from pydantic import BaseModel


class IngredientDB(BaseModel):
    id: int
    name: str
    measurement_unit: str

    class Config:
        from_attributes = True
