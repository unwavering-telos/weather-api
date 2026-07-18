import json
import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import redis

load_dotenv()

redis_client = redis.Redis(
    host="localhost",
    port=6380,
    decode_responses=True,
)


app = FastAPI()

API_KEY = os.getenv("MY_WEATHER_API_KEY")
BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"


def fetch_weather(city):

    cashed = redis_client.get(city)
    if cashed:
        return json.loads(cashed)

    url = f"{BASE_URL}/{city}?key={API_KEY}&unitGroup=metric&include=current"

    try:
        response = requests.get(url, timeout=5)
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=503, detail="Weather service is currently unavailable"
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail=f"City not found: {city}",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Weather service returned an error",
        )
    data = response.json()
    result = {
        "city": city,
        "weather": data["currentConditions"]["conditions"],
        "temp": data["currentConditions"]["temp"],
    }
    redis_client.set(city, json.dumps(result), ex=3600)
    return result


@app.get("/weather/{city}")
def get_weather(city):
    data = fetch_weather(city)
    if data is None:
        return {"error": "city name is not found"}
    return data
