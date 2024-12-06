from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from app import assistant_chat


app = FastAPI()

class Question(BaseModel):
   query: str

@app.post("/chat")
async def root(question: Question):
   return assistant_chat(question.query)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)