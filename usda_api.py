import os
import requests

# Puedes sobrescribir con la variable de entorno USDA_API_KEY
API_KEY = os.getenv("USDA_API_KEY", "DkRmZu9FxAhQFL1DCgLWoMG1z0wwBVUzcOD2sJ0J")
BASE_URL = "https://api.nal.usda.gov/fdc/v1"

def buscar_alimento(query, pageSize=5):
    """
    Busca alimentos por texto usando /foods/search.
    Devuelve el JSON de respuesta (contendrá clave 'foods' con resultados).
    """
    try:
        url = f"{BASE_URL}/foods/search?api_key={API_KEY}"
        payload = {"query": query, "pageSize": pageSize}
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {"foods": []}

def obtener_nutrientes(fdc_id):
    """
    Obtiene detalle de alimento por fdcId usando /food/{fdcId}.
    Devuelve el JSON de respuesta (contendrá 'foodNutrients').
    """
    try:
        url = f"{BASE_URL}/food/{fdc_id}?api_key={API_KEY}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {"foodNutrients": []}
