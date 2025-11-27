# apis/spoonacular.py
import os
import requests

API_KEY = os.getenv("SPOONACULAR_API_KEY")
BASE = "https://api.spoonacular.com"

def search_recipes(query, number=12):
    url = f"{BASE}/recipes/complexSearch"
    params = {"apiKey": API_KEY, "query": query, "number": number, "addRecipeInformation": False}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def get_recipe_info(spoon_id):
    """
    Obtiene información completa de receta (ingredients, amounts, servings, instructions, image).
    """
    url = f"{BASE}/recipes/{spoon_id}/information"
    params = {"apiKey": API_KEY, "includeNutrition": False}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()
