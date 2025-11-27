from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests

API_KEY = "DkRmZu9FxAhQFL1DCgLWoMG1z0wwBVUzcOD2sJ0J" 

BASE_URL = "https://api.nal.usda.gov/fdc/v1"

from flask import Flask, render_template, request, session, redirect, url_for, flash
from spoonacular import search_recipes, get_recipe_info
import re



app = Flask(__name__)
app.config['SECRET_KEY'] = 'theswordoftarnished'

cazadores = {
    'correo@gmail.com': {
        'password': '1234',
        'nombre': 'administrador',
        'profile': {
            'peso': 79,
            'altura': 170,
            'edad': 17,
            'sexo': 'Male',
            'actividad': 'Media',
            'objetivo': 70.1,
            'pasos': 10000
        }
    }
}

@app.route('/')
def home():
    if not session.get('logueado') and not session.get('seen_welcome'):
        session['seen_welcome'] = True
        return render_template('welcome.html')

    return render_template('inicio.html')


@app.route('/perfil')
def perfil():

    email = session.get('usuario_email')
    entrada = cazadores.get(email)
    registro = entrada.get('profile', {}) if entrada else {}

    usuario = {}
    if entrada:
        usuario['nombre'] = entrada.get('nombre')
    for k, v in registro.items():
        usuario[k] = v

    if 'apellido' in usuario and 'apellidos' not in usuario:
        usuario['apellidos'] = usuario.get('apellido')

    try:
        peso = float(usuario.get('peso') or 0)
        altura = float(usuario.get('altura') or 0)
        if peso > 0 and altura > 0:
            usuario['imc'] = round(peso / ((altura / 100) ** 2), 1)
        else:
            usuario['imc'] = None
    except Exception:
        usuario['imc'] = None

    try:
        edad = int(usuario.get('edad') or 0)
        sexo = (usuario.get('sexo') or '').strip().lower()
        if peso > 0 and altura > 0 and edad > 0:
            if sexo.startswith('m') or sexo in ('male', 'masculino', 'hombre'):
                tmb = 88.362 + (13.397 * peso) + (4.799 * altura) - (5.677 * edad)
            else:
                tmb = 447.593 + (9.247 * peso) + (3.098 * altura) - (4.330 * edad)
            usuario['tmb'] = int(round(tmb))
        else:
            usuario['tmb'] = None
    except Exception:
        usuario['tmb'] = None

    actividad = (usuario.get('actividad') or '').lower()
    factor = None
    if 'sed' in actividad or 'baja' in actividad:
        factor = 1.2
    elif 'lig' in actividad:
        factor = 1.375
    elif 'mod' in actividad or 'media' in actividad:
        factor = 1.55
    elif 'act' in actividad or 'activo' in actividad:
        factor = 1.725
    elif 'atleta' in actividad:
        factor = 1.9
    if usuario.get('tmb') and factor:
        usuario['gct'] = int(round(usuario['tmb'] * factor))
    else:
        usuario['gct'] = None

    try:
        altura_cm = float(usuario.get('altura') or 0)
        altura_in = altura_cm / 2.54
        if altura_in > 0:
            if sexo.startswith('m') or sexo in ('male', 'masculino', 'hombre'):
                peso_ideal = 50.0 + 2.3 * (altura_in - 60.0)
            else:
                peso_ideal = 45.5 + 2.3 * (altura_in - 60.0)
            usuario['peso_ideal'] = round(peso_ideal, 1)
        else:
            usuario['peso_ideal'] = None
    except Exception:
        usuario['peso_ideal'] = None

    if usuario.get('gct'):
        kcal = usuario['gct']
        usuario['macros_prote'] = int(round((0.2 * kcal) / 4))
        usuario['macros_carbs'] = int(round((0.5 * kcal) / 4))
        usuario['macros_grasas'] = int(round((0.3 * kcal) / 9))
    else:
        usuario['macros_prote'] = usuario['macros_carbs'] = usuario['macros_grasas'] = None

    return render_template('perfil.html', usuario=usuario, registro=registro)

@app.route('/iniciar', methods=['GET', 'POST'])
def iniciar():
    if session.get('logueado'):
        return redirect(url_for('home'))

    if request.method == 'POST':
        email_input = request.form.get('email', '').strip()
        email = email_input.lower()
        password = request.form.get('password', '')

        if not email_input or not password:
            flash('Que el cazador ingrese su correo y contraseña', 'error')
        elif email in cazadores:
            usuario = cazadores[email]
            if usuario['password'] == password:
                session['usuario_email'] = email
                session['cazador'] = usuario.get('nombre', 'Usuario')
                session['logueado'] = True
                flash(f"El cazador {usuario['nombre']} ha despertado nuevamente...", "success")
                return redirect(url_for('home'))
            else:
                flash('Contraseña equivocada', 'error')
        else:
            flash('usuario no encontrado', 'error')

    return render_template('iniciar.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    total_steps = 17
    if request.method == 'POST' and request.form.get('email') and request.form.get('password') and request.form.get('nombre'):
        campos = [
            "email", "password", "nombre", "apellido", "edad", "sexo", "peso",
            "altura", "actividad", "objetivo", "alergias", "intolerancias",
            "dieta", "alimentos_no_gustan", "experiencia_cocina",
            "condiciones_medicas", "acumular_calorias"
        ]
        registro = {}
        for c in campos:
            registro[c] = request.form.get(c, '').strip()

        email_raw = registro.get('email', '')
        email = email_raw.strip().lower()
        nombre = registro.get('nombre', 'Usuario')
        password = registro.get('password', '')

        if not email or not password:
            flash('Faltan email o contraseña en los datos de registro.', 'error')
            return redirect(url_for('registro'))

        if email in cazadores:
            flash('Ya existe una cuenta con ese correo.', 'error')
            return redirect(url_for('registro'))

        profile = registro.copy()
        profile.pop('email', None)
        profile.pop('password', None)

        cazadores[email] = {
            'password': password,
            'nombre': nombre,
            'profile': profile
        }

        session['usuario_email'] = email
        session['cazador'] = nombre
        session['logueado'] = True
        flash(f"Cuenta creada. Bienvenido {nombre}.", 'success')
        return redirect(url_for('perfil'))

    try:
        step = int(request.args.get('step', 1))
    except ValueError:
        step = 1

    registro = session.get('registro', {})

    if request.method == 'POST':
        campos = [
            "email", "password", "nombre", "apellido", "edad", "sexo", "peso",
            "altura", "actividad", "objetivo", "alergias", "intolerancias",
            "dieta", "alimentos_no_gustan", "experiencia_cocina",
            "condiciones_medicas", "acumular_calorias"
        ]

        campo_actual = campos[step - 1] if step <= len(campos) else None
        if campo_actual:
            registro[campo_actual] = request.form.get(campo_actual, '').strip()
        session['registro'] = registro

        if step < total_steps:
            return redirect(url_for('registro', step=step + 1))

        action = request.form.get('action')
        if action == 'agregar':
            email_raw = registro.get('email', '')
            email = email_raw.strip().lower()
            nombre = registro.get('nombre', 'Usuario')
            password = registro.get('password', '')
            if not email or not password:
                flash('Faltan email o contraseña en los datos de registro.', 'error')
                return redirect(url_for('registro', step=1))
            if email in cazadores:
                flash('Ya existe una cuenta con ese correo.', 'error')
                return redirect(url_for('registro', step=1))

            profile = registro.copy()
            profile.pop('email', None)
            profile.pop('password', None)

            cazadores[email] = {
                'password': password,
                'nombre': nombre,
                'profile': profile
            }

            session['usuario_email'] = email
            session['cazador'] = nombre
            session['logueado'] = True
            session.pop('registro', None)
            flash(f"Cuenta creada. Bienvenido {nombre}.", 'success')
            return redirect(url_for('perfil'))
        else:
            session.pop('registro', None)
            flash('Registro omitido. Puedes completar el perfil más tarde.', 'info')
            return redirect(url_for('home'))

    return render_template('registro.html', step=step, total_steps=total_steps, registro=registro)

@app.route('/cerrar')
def cerrar():
    session.clear()
    flash("El cazador ha regresado a su sueño...", "danger")
    return redirect(url_for('home'))

@app.route('/registro_alimentos')
def registro_alimentos():

    return redirect(url_for('perfil'))

@app.route('/calculadora_IMC', methods=['GET', 'POST'])
def calculadora_IMC():
    imc = None
    peso = None
    altura = None
    if request.method == 'POST':
        try:
            peso = float(request.form.get('peso') or 0)
            altura = float(request.form.get('altura') or 0)
            if peso > 0 and altura > 0:
                imc = peso / ((altura / 100) ** 2)
        except ValueError:
            imc = None
    return render_template('calculadora_IMC.html', imc=imc, peso=peso, altura=altura)

@app.route('/calculadora_TMB', methods=['GET', 'POST'])
def calculadora_TMB():
    tmb = None
    peso = None
    altura = None
    edad = None
    sexo = ''
    if request.method == 'POST':
        try:
            peso = float(request.form.get('peso') or 0)
            altura = float(request.form.get('altura') or 0)
            edad = int(request.form.get('edad') or 0)
            sexo = request.form.get('sexo', '')
            if peso > 0 and altura > 0 and edad > 0:
                if sexo == 'Male':
                    tmb = 88.362 + (13.397 * peso) + (4.799 * altura) - (5.677 * edad)
                elif sexo == 'Female':
                    tmb = 447.593 + (9.247 * peso) + (3.098 * altura) - (4.330 * edad)
        except ValueError:
            tmb = None
    return render_template('calculadora_TMB.html', tmb=tmb, peso=peso, altura=altura, edad=edad, sexo=sexo)

@app.route('/calculadora_GCT', methods=['GET', 'POST'])
def calculadora_GCT():
    gct = None
    tmb = None
    actividad = ''
    if request.method == 'POST':
        try:
            tmb = float(request.form.get('tmb') or 0)
            actividad = request.form.get('actividad', '')
            if tmb and actividad:
                if actividad == 'Baja':
                    gct = tmb * 1.2
                elif actividad == 'Media':
                    gct = tmb * 1.55
                elif actividad == 'Alta':
                    gct = tmb * 1.9
        except ValueError:
            gct = None
    return render_template('calculadora_GCT.html', gct=gct, tmb=tmb, actividad=actividad)

@app.route('/calculadora_PMI', methods=['GET', 'POST'])
def calculadora_PMI():
    pmi = None
    sexo = ''
    altura = None
    altura_in = None
    if request.method == 'POST':
        try:
            altura = float(request.form.get('altura') or 0)  # cm
            sexo = request.form.get('sexo', '')
            if altura and sexo:
                altura_in = altura / 2.54
                if sexo == 'Male':
                    pmi = 50.0 + 2.3 * (altura_in - 60.0)
                elif sexo == 'Female':
                    pmi = 45.5 + 2.3 * (altura_in - 60.0)
        except ValueError:
            pmi = None
    return render_template('calculadora_PMI.html', pmi=pmi, sexo=sexo, altura=altura)


@app.route("/articulos")
def articulos():
    return render_template("articulos.html")


from usda_api import buscar_alimento, obtener_nutrientes

@app.route("/analizador", methods=["GET", "POST"])
def analizador():
    if request.method == "POST":
        texto = request.form.get("ingredientes", "")
        try:
            porciones = int(request.form.get("porciones", 1)) or 1
        except Exception:
            porciones = 1

        lineas = [l.strip() for l in texto.splitlines() if l.strip()]

        resultados = []
        total_cal = total_prot = total_carbs = total_fat = 0.0

        def _find_value(nutrients, keywords):
            for n in nutrients:
                # varios formatos posibles en la API USDA
                name = n.get("nutrientName") or (n.get("nutrient") or {}).get("name") or n.get("name") or ""
                name_l = str(name).lower()
                if any(k in name_l for k in keywords):
                    val = n.get("value") or n.get("amount") or 0
                    try:
                        return float(val)
                    except Exception:
                        return 0.0
            return 0.0

        for linea in lineas:
            # buscar el alimento (usar la primera coincidencia)
            busq = buscar_alimento(linea, pageSize=1)
            foods = busq.get("foods") or []
            if not foods:
                resultados.append({
                    "nombre": linea,
                    "cal": 0.0, "prot": 0.0, "carbs": 0.0, "fat": 0.0,
                    "fuente": "no encontrado"
                })
                continue

            food = foods[0]
            fdc = food.get("fdcId") or food.get("fdcId")  # robustez
            data = obtener_nutrientes(fdc) if fdc else food

            nutrients = data.get("foodNutrients") or data.get("foodNutrients", []) or []

            cal = _find_value(nutrients, ["energy", "kcal", "enerc"])
            prot = _find_value(nutrients, ["protein"])
            carbs = _find_value(nutrients, ["carbohyd", "carbo", "carb"])
            fat = _find_value(nutrients, ["fat", "lipid", "total lipid"])

            total_cal += cal
            total_prot += prot
            total_carbs += carbs
            total_fat += fat

            resultados.append({
                "nombre": food.get("description") or linea,
                "cal": round(cal, 2),
                "prot": round(prot, 2),
                "carbs": round(carbs, 2),
                "fat": round(fat, 2),
                "fuente": "USDA"
            })

        porcion = {
            "cal": (total_cal / porciones) if porciones else 0,
            "prot": (total_prot / porciones) if porciones else 0,
            "carbs": (total_carbs / porciones) if porciones else 0,
            "fat": (total_fat / porciones) if porciones else 0,
        }

        return render_template("analizador.html",
                               resultados=resultados,
                               totales={
                                   "cal": round(total_cal, 2),
                                   "prot": round(total_prot, 2),
                                   "carbs": round(total_carbs, 2),
                                   "fat": round(total_fat, 2)
                               },
                               porcion=porcion,
                               porciones=porciones
                               )

    return render_template("analizador.html")


@app.route("/recetas", methods=["GET", "POST"])
def recetas():
    recetas = None
    if request.method == "POST":
        q = request.form.get("query", "").strip()
        if q:
            data = search_recipes(q, number=12)
            recetas = []
            for r in data.get("results", []):
                recetas.append({
                    "id": r.get("id"),
                    "nombre": r.get("title"),
                    "imagen": r.get("image"),
                    "descripcion": r.get("summary")[:140] if r.get("summary") else "",
                    "tiempo": r.get("readyInMinutes") or ""
                })
    return render_template("recetas.html", recetas=recetas)

@app.route("/receta/<int:spoon_id>")
def receta_detalle(spoon_id):
    info = get_recipe_info(spoon_id)

    receta = {
        "id": spoon_id,
        "nombre": info.get("title"),
        "imagen": info.get("image"),
        "servings": info.get("servings") or 1,
        "readyInMinutes": info.get("readyInMinutes"),
        "instructions": info.get("instructions"),
        "ingredients": []
    }

    nutrientes_por_ingrediente = []
    for ing in info.get("extendedIngredients", []):
        original = ing.get("originalString") or f"{ing.get('amount')} {ing.get('unit')} {ing.get('name')}"
        query_text = f"{ing.get('amount', '')} {ing.get('unit', '')} {ing.get('name', '')}".strip()

        
        search = search_foods(query_text, pageSize=2)
        foods = search.get("foods", [])
        chosen = None
        if foods:
            chosen = foods[0]    
            fdc_id = chosen.get("fdcId")
            food_detail = get_food(fdc_id)
            nutrients = extract_nutrients(food_detail)

            cantidad = ing.get("amount", 1)
            unidad = ing.get("unit", "").lower()

            gramos = None
            if unidad in ("g", "gram", "grams"):
                gramos = float(cantidad)
            elif unidad in ("kg", "kilogram", "kilograms"):
                gramos = float(cantidad) * 1000
            elif unidad in ("mg", "milligram"):
                gramos = float(cantidad) / 1000
            elif unidad in ("cup", "cups"):
                gramos = float(cantidad) * 240
            elif unidad in ("tbsp", "tablespoon", "tablespoons"):
                gramos = float(cantidad) * 15
            elif unidad in ("tsp", "teaspoon", "teaspoons"):
                gramos = float(cantidad) * 5
            else:
                gramos = None

            escala = None
            if gramos is not None:
                escala = gramos / 100.0
            else:
                escala = 1.0

            scaled = {
                "original": original,
                "chosen_description": chosen.get("description"),
                "gramos": gramos,
                "cal": round(nutrients["energy"] * escala, 2),
                "prot": round(nutrients["protein"] * escala, 2),
                "carbs": round(nutrients["carbs"] * escala, 2),
                "fat": round(nutrients["fat"] * escala, 2)
            }
        else:
            scaled = {
                "original": original,
                "chosen_description": None,
                "gramos": None,
                "cal": 0,
                "prot": 0,
                "carbs": 0,
                "fat": 0
            }

        nutrientes_por_ingrediente.append(scaled)
        receta["ingredients"].append({"original": original})

    total_cal = sum(i["cal"] for i in nutrientes_por_ingrediente)
    total_prot = sum(i["prot"] for i in nutrientes_por_ingrediente)
    total_carbs = sum(i["carbs"] for i in nutrientes_por_ingrediente)
    total_fat = sum(i["fat"] for i in nutrientes_por_ingrediente)

    receta["nutrientes"] = {
        "cal": round(total_cal, 2),
        "prot": round(total_prot, 2),
        "carbs": round(total_carbs, 2),
        "fat": round(total_fat, 2)
    }

    receta["ingredientes_nut"] = nutrientes_por_ingrediente

    return render_template("receta_detalle.html", receta=receta)

@app.route('/ComoCal')
def como_cal():
    return render_template('comocal.html')
@app.route('/Macros')
def Macros():
    return render_template('Macros.html')
@app.route('/NEAT')
def NEAT():
    return render_template('NEAT.html')
@app.route('/QueIMC')
def QueIMC():
    return render_template('QueIMC.html')
@app.route('/Entrenamiento')
def Entrenamiento():
    return render_template('Entrenamiento.html')
@app.route('/sueño')
def sueño():
    return render_template('sueño.html')


if __name__ == '__main__':
    app.run(debug=True)