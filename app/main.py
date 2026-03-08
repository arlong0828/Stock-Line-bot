from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
def home():
    return {"status": "running"}

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print(body)
    return {"status": "ok"}