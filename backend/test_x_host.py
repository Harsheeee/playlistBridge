from fastapi import FastAPI, Request
app = FastAPI()

@app.get("/")
def read_root(request: Request):
    return {
        "host": request.headers.get("host"),
        "x_forwarded_host": request.headers.get("x-forwarded-host")
    }
