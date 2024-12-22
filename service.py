from fastapi import FastAPI, Response, Request
import uvicorn
import logging
from starlette.background import BackgroundTask
from logging import handlers
import psycopg2, json
from psycopg2.extras import RealDictCursor


app = FastAPI()

def log_info(req_body, res_body):
    logging.info(req_body)
    logging.info(res_body)


@app.middleware('http')
async def some_middleware(request: Request, call_next):
    req_body = await request.body()
    response = await call_next(request)
    
    res_body = b''
    async for chunk in response.body_iterator:
        res_body += chunk
    
    task = BackgroundTask(log_info, req_body, res_body)
    return Response(content=res_body, status_code=response.status_code, 
        headers=dict(response.headers), media_type=response.media_type, background=task)


@app.get("/hello")
async def root():
    return {"body": "123"}

@app.get("/healthcheck")
async def healthcheck():
    return "OK"

@app.get("/database")
async def database():
    conn = psycopg2.connect(dbname='tester', user='postgres', password='postgres')
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute("select * from man")
        rows = curs.fetchall()
        return rows

@app.get('/')
def main(payload):
    return payload

if __name__ == '__main__':
    uvicorn.run(app, log_config='log.ini')