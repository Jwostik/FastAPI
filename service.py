from fastapi import FastAPI, HTTPException, Request
import psycopg2, uvicorn, os, hashlib, jwt, datetime
from pydantic import BaseModel


app = FastAPI()


class User(BaseModel):
    login: str
    password: str
    description: str

class Auth(BaseModel):
    login: str
    password: str

key = "secret"


@app.get("/healthcheck")
async def healthcheck():
    return "OK"


@app.post("/users")
async def users(data: User):
    conn = psycopg2.connect(dbname='tester', user='postgres', password='postgres')
    with conn.cursor() as curs:
        curs.execute("select count(*) from credentials where login = %s", [data.login])
        count, = curs.fetchone()
        if count > 0:
            raise HTTPException(status_code=409, detail="Login has already used")
        salt = os.urandom(32)
        hash = hashlib.pbkdf2_hmac('sha256', data.password.encode('utf-8'), salt, 100000)
        curs.execute("insert into credentials (login, password_hash, salt) values (%s, %s, %s)", [data.login, hash, salt])
        curs.execute("select account_id from credentials where login = %s", [data.login])
        account_id, = curs.fetchone()
        curs.execute("insert into user_info (account_id, description) values (%s, %s)", [account_id, data.description]) 
        conn.commit()
    return account_id
    
@app.post("/auth")
async def auth(data: Auth):
    conn = psycopg2.connect(dbname='tester', user='postgres', password='postgres')
    with conn.cursor() as curs:
        curs.execute("select count(*) from credentials where login = %s", [data.login])
        count, = curs.fetchone()
        if count == 0:
            raise HTTPException(status_code=401, detail="Incorrect login")
        curs.execute("select password_hash, salt, account_id from credentials where login = %s", [data.login])
        correct_hash, salt, account_id = curs.fetchone()
        hash = hashlib.pbkdf2_hmac('sha256', data.password.encode('utf-8'), salt, 100000)
        if bytes(correct_hash) != hash:
            raise HTTPException(status_code=401, detail="Incorrect password")
        payload = {"account_id": account_id, "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=1)}
        token = jwt.encode(payload, key)
    return token

@app.get("/users/{account_id}")
async def get_user_by_account_id(request: Request, account_id):
    if not account_id.isdigit():
        raise HTTPException(status_code=401, detail="Invalid account id")
    token = request.headers.get('x-auth-header')
    if not token:
        raise HTTPException(status_code=401, detail="No token")
    try:
        payload = jwt.decode(token, key, algorithms='HS256')
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    if payload['account_id'] != int(account_id):
        raise HTTPException(status_code=401, detail="Invalid account")
    conn = psycopg2.connect(dbname='tester', user='postgres', password='postgres')
    with conn.cursor() as curs:
        curs.execute("select description from user_info where account_id = %s", [payload['account_id']])
        description, = curs.fetchone()
    return description


if __name__ == '__main__':
    uvicorn.run(app)
