from fastapi import FastAPI, HTTPException
import psycopg2, uvicorn
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel


app = FastAPI()


class User(BaseModel):
    login: str
    password: str


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


@app.post("/users")
async def users(data: User):
    conn = psycopg2.connect(dbname='tester', user='postgres', password='postgres')
    with conn.cursor(cursor_factory=RealDictCursor) as curs:
        curs.execute("select count(*) from credentials where login=" + data.login)
        count = curs.fetch()
        print(count)
#    if data.name == 2:
#        raise HTTPException(status_code=409, detail="Login has already used")
    return data


if __name__ == '__main__':
    uvicorn.run(app)
