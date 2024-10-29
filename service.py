from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/hello")
async def root():
    return {"body": "123"}

if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='localhost', log_config=f"log.ini")