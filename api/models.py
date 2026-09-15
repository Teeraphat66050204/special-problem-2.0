from sqlmodel import SQLModel, Field
from typing import Optional
from sqlalchemy import Column
from pgvector.sqlalchemy import Vector

class ProjectDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author: str
    year: str
    wiki_content: str 
    
class DocumentChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projectdocument.id")
    chunk_text: str
    embedding: list[float] = Field(sa_column=Column(Vector(768)))