from fastapi import FastAPI, Path, status
from fastapi.responses import JSONResponse
from datetime import datetime
import redis.asyncio as redis

from pydantic import BaseModel, field_validator

class UserDOB(BaseModel):
    dateOfBirth: datetime

    @field_validator('dateOfBirth')
    def date_must_be_past(cls, v):
        if v >= datetime.today():
            raise ValueError('dateOfBirth must be a date before today')
        return v

redis_client = redis.Redis(host='localhost', port=6379, db=0)

app = FastAPI()

@app.get("/hello/{username}", response_model=dict)
async def read_user_birthday(username: str = Path(..., regex="^[a-zA-Z]+$")):
    user_dob_str = await redis_client.get(username)
    if not user_dob_str:
        return JSONResponse(content={"message": "User not found"}, status_code=404)

    user_dob = datetime.strptime(user_dob_str.decode("utf-8"), "%Y-%m-%d")
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    this_year_birthday = user_dob.replace(year=today.year)

    if this_year_birthday < today:
        this_year_birthday = this_year_birthday.replace(year=today.year + 1)

    days_until_birthday = (this_year_birthday - today).days

    if days_until_birthday == 0:
        message = f"Hello, {username}! Happy birthday!"
    else:
        message = f"Hello, {username}! Your birthday is in {days_until_birthday} day(s)"

    return JSONResponse(content={"message": message})

@app.put("/hello/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_dob(username: str = Path(..., regex="^[a-zA-Z]+$"), user_dob: UserDOB = None):
    datetime_str = user_dob.dateOfBirth.strftime("%Y-%m-%d")
    await redis_client.set(username, datetime_str)
    return
