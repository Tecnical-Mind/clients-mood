import uuid

from pydantic import BaseModel, EmailStr


class RequestLinkIn(BaseModel):
    email: EmailStr


class RequestLinkOut(BaseModel):
    message: str = "If that email is valid, a sign-in link has been sent."


class MeOut(BaseModel):
    id: uuid.UUID
    email: str

    model_config = {"from_attributes": True}
