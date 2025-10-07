from fastapi import FastAPI # pyright: ignore[reportMissingImports]
from pydantic import BaseModel # pyright: ignore[reportMissingImports]
from xuanji_ai_main import run_xuanji_ai

app = FastAPI()

class XuanjiRequest(BaseModel):
    input: str

@app.post("/run_xuanji_ai")
async def run_xuanji_ai_api(req: XuanjiRequest):
    result = run_xuanji_ai(req.input)
    return {"result": result}

@app.get("/")
async def root():
    return {"msg": "XuanjiAI2.0 API is running."}
