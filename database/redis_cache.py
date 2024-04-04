from functools import wraps

from fastapi.responses import JSONResponse
from redis import Redis

r = Redis(host="cache", port=6379, db=0)


def cache_utils(func):
    @wraps(func)
    async def wrapper(question, user):
        response = [
            {
                phrase.strip(): await r.hget(
                    name=f"user_id->{user.get("id")}", key=phrase.strip()
                ).decode()
            }
            for phrase in question.phrase
            if r.hexists(key=phrase.strip(), name=f"user_id->{user.get("id")}")
        ]
        if response:
            return JSONResponse(content=response, status_code=200)
        return func(question, user)

    return wrapper
