from pydantic import BaseModel

class JobRequest(BaseModel):
    dir: str
    

class JobResponse(BaseModel):
    message: str
    status: str