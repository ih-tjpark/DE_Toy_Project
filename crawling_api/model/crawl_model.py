from pydantic import BaseModel

class CrawlRequest(BaseModel):
    keyword: str
    max_links: int

class crawlResponse(BaseModel):
    message: str
    status: str