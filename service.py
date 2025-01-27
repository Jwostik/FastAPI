from fastapi import FastAPI, HTTPException
import psycopg2, uvicorn, os, hashlib
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel


app = FastAPI()


class User(BaseModel):
    login: str
    password: str
    description: str

class Auth(BaseModel):
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
    with conn.cursor() as curs:
        curs.execute("select count(*) from credentials where login = %s", [str(data.login)])
        count = curs.fetchone()
        if count[0] > 0:
            raise HTTPException(status_code=409, detail="Login has already used")
        salt = os.urandom(32)
        hash = hashlib.pbkdf2_hmac('sha256', data.password.encode('utf-8'), salt, 100000)
        curs.execute("insert into credentials (login, password_hash, salt) values (%s, %s, %s)", [str(data.login), str(hash), str(salt)])
        curs.execute("select account_id from credentials where login = %s", [str(data.login)])
        account_id = curs.fetchone()
        curs.execute("insert into user_info (account_id, description) values (%s, %s)", [account_id[0], str(data.description)])
        conn.commit()
        return account_id[0]
    
@app.post("/auth")
async def users(data: Auth):
    conn = psycopg2.connect(dbname='tester', user='postgres', password='postgres')
    with conn.cursor() as curs:
        curs.execute("select count(*) from credentials where login = %s", [str(data.login)])
        count = curs.fetchone()
        if count[0] > 0:
            raise HTTPException(status_code=401, detail="Incorrect login")



if __name__ == '__main__':
    uvicorn.run(app)
