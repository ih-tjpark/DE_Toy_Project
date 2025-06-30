from pydantic import BaseModel

class JobRequest(BaseModel):
    product_code: str
    reviews: list
    

class JobResponse(BaseModel):
    message: str
    status: str