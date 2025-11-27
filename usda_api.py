import requests
import os

API_KEY = os.getenv("DkRmZu9FxAhQFL1DCgLWoMG1z0wwBVUzcOD2sJ0J") 

BASE_URL = "https://api.nal.usda.gov/fdc/v1"

def buscar_alimento(nombre):
    url = f"{BASE_URL}/foods/search"
    params = {
        "api_key": API_KEY,
        "query": nombre,
        "pageSize": 3
    }
    res = requests.get(url, params=params)
    return res.json()

def obtener_nutrientes(fdc_id):
    url = f"{BASE_URL}/food/{fdc_id}"
    params = {"api_key": API_KEY}
    res = requests.get(url, params=params)
    return res.json()
