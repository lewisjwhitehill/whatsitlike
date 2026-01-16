from fastapi import FastAPI, HTTPException
from llm.assistant import formulate_response

app = FastAPI()

@app.get("/weather")
async def weather(query: str):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")

    try:
        summary = formulate_response(query)
    except Exception as e:
        # TODO: add logging here if you want
        raise HTTPException(status_code=500, detail="Failed to generate weather summary")

    return {"summary": summary}
