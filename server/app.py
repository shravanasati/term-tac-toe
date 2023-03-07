from fastapi import FastAPI
from fastapi.responses import HTMLResponse


app = FastAPI()


@app.get("/")
async def root():
    return HTMLResponse("The website is under development :)")

