from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['MYSQL_DB'] = 'calborne'   # <-- cambiado de 'usuarios' a 'calborne'
app.config['MYSQL_HOST'] = '127.0.0.1'  # en vez de 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'usuarios'

mysql = MySQL(app)
app.config['MYSQL_DB'] = 'calborne'  
API_BASE = "https://api.nal.usda.gov/fdc/v1/"
API_KEY = "QweiYpuEmJTfQlcfZLdquUSeiCqxe7sGaLQo2OaJ"


def email_existe(email):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id FROM usuarios WHERE email = %s', (email,))
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists
    except Exception as e:
        print(f"Error verificando email: {e}")
        return False


def obtener_usuario_por_email(email):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, email, password, nombre FROM usuarios WHERE email = %s', (email,))
        row = cursor.fetchone()
        cursor.close()
        return row
    except Exception as e:
        print(f"error verificando usuario: {e}")
        return None




# Ruta principal: muestra bienvenida la primera vez y luego inicio.
@app.route('/')
def home():
    if not session.get('logueado') and not session.get('seen_welcome'):
        session['seen_welcome'] = True
        return render_template('welcome.html')

    return render_template('inicio.html')


# Página de perfil: construye un diccionario 'usuario' con cálculos como IMC, TMB, GCT, peso ideal y macros.
@app.route('/perfil')
def perfil():
    if 'usuario_email' not in session:
        flash("Inicia sesión para ver tu perfil", "error")
        return redirect(url_for('iniciar'))

    usuario_id = session.get('usuario_id')
    cur = mysql.connection.cursor()

    cur.execute("SELECT id, email, nombre, paterno, materno FROM usuarios WHERE id=%s", (usuario_id,))
    usuario = cur.fetchone()

    cur.execute("SELECT altura_cm, peso_actual_kg, peso_objetivo_kg, nivel_actividad FROM perfiles_usuario WHERE usuario_id=%s", (usuario_id,))
    salud = cur.fetchone()

    cur.close()

    perfil_dic = {}
    if usuario:
        perfil_dic['nombre'] = usuario[2]
        perfil_dic['apellidos'] = " ".join([p for p in usuario[3:] if p])
    if salud:
        perfil_dic['altura'] = salud[0]
        perfil_dic['peso'] = salud[1]
        perfil_dic['actividad'] = salud[3]

    return render_template("perfil.html", usuario=perfil_dic, registro={})
# Ruta de inicio de sesión: valida credenciales contra el dict 'cazadores'

@app.route('/iniciar', methods=['GET', 'POST'])
def iniciar():
    # muestra el formulario y procesa login
    if session.get('logueado'):
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Por favor ingrese email y contraseña', 'danger')
            return render_template('iniciar.html')

        usuario = obtener_usuario_por_email(email)
        if usuario and check_password_hash(usuario[2], password):
            session['usuario_id'] = usuario[0]
            session['usuario_nombre'] = usuario[3]
            session['usuario_email'] = usuario[1]
            session['logueado'] = True
            flash(f'¡Bienvenido {usuario[3]}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Email o contraseña incorrectos', 'danger')
            return render_template('iniciar.html')

    return render_template('iniciar.html')
# Registro: permite registro por pasos y guarda en memoria en 'cazadores'

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get("nombre")
        paterno = request.form.get("paterno")
        materno = request.form.get("materno")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password")
        fecha_nacimiento = request.form.get('fecha_nacimiento')
        genero = request.form.get("genero")
        telefono = request.form.get("telefono")

        # Validar que coincidan las contraseñas
        if email_existe(email):
            flash("El correo ya está registrado", "danger")
            return redirect(url_for("registro"))

        try:
            cursor = mysql.connection.cursor()
            hashed_password = generate_password_hash(password)

            cursor.execute(
                'INSERT INTO usuarios (email, password, nombre, paterno, materno, fecha_nacimiento, genero, telefono) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (email, hashed_password, nombre, paterno, materno, fecha_nacimiento, genero, telefono)
            )

            mysql.connection.commit()
            cursor.close()

            flash("¡Registro exitoso! Inicia sesión.", "success")
            return redirect(url_for("iniciar"))

        except Exception as e:
            flash(f"Error al registrar usuario: {str(e)}", "danger")
            return redirect(url_for("registro"))

    # GET: mostrar formulario
    dias = list(range(1, 32))
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    año_actual = datetime.now().year
    años = list(range(año_actual, 1905, -1))

    return render_template("registro.html", dias=dias, meses=meses, años=años)


# Cerrar sesión: limpiar la sesión
@app.route('/cerrar')
def cerrar():
    session.clear()
    flash("El cazador ha regresado a su sueño...", "danger")
    return redirect(url_for('home'))

@app.route('/registro_alimentos')
def registro_alimentos():
    # Actualmente redirige al perfil; placeholder para futura funcionalidad
    return redirect(url_for('perfil'))

# Calculadoras: IMC, TMB, GCT, PMI (cada una calcula en POST y muestra resultado en plantilla)
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


# Rutas estáticas para páginas informativas
@app.route("/articulos")
def articulos():
    return render_template("articulos.html")


# Funciones de análisis de alimentos usando la API USDA (importadas)
from usda_api import buscar_alimento, obtener_nutrientes

# Analizador: recibe texto con ingredientes (uno por línea), consulta USDA y suma nutrientes.
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

        # Función auxiliar para localizar el nutriente adecuado en respuestas de USDA
        def _find_value(nutrients, keywords):
            for n in nutrients:
                # soportar varios nombres que vienen en la API
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
            # Buscar alimento y tomar la primera coincidencia
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

            # Buscar calorías, proteínas, carbohidratos y grasas con palabras clave
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

        # Calcular porción promedio
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


# Recetas: buscar con spoonacular y mostrar lista

@app.route('/recetas', methods=['POST'])
def recetas():
    receta_texto = request.form.get("receta", "").strip()

    if not receta_texto:
        flash("Ingresa una receta para analizar.", "error")
        return redirect(url_for("analizadorRecetas"))

    lineas = receta_texto.split("\n")
    ingredientes = []
    nutrientes_totales = {}

    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue

        partes = linea.split(" ", 1)
        try:
            cantidad = float(partes[0])
            alimento = partes[1] if len(partes) > 1 else partes[0]
        except:
            cantidad = 1
            alimento = linea

        alimento = alimento.lower()
        url_busqueda = f"{API_BASE}foods/search?query={alimento}&api_key={API_KEY}"
        res = requests.get(url_busqueda, timeout=10)
        if res.status_code != 200:
            continue
        data = res.json()
        if "foods" not in data or len(data["foods"]) == 0:
            continue

        fdc_id = data["foods"][0]["fdcId"]
        detalle = requests.get(f"{API_BASE}food/{fdc_id}?api_key={API_KEY}", timeout=10).json()
        nutrientes = detalle.get("foodNutrients", [])

        for n in nutrientes:
            nombre_nutriente = n.get("nutrient", {}).get("name")
            unidad = n.get("nutrient", {}).get("unitName")
            cantidad_base = n.get("amount", 0)

            clave = f"{nombre_nutriente} ({unidad})"
            nutrientes_totales[clave] = nutrientes_totales.get(clave, 0) + (cantidad_base * cantidad)

        ingredientes.append(f"{cantidad} {alimento}")

    return render_template("resultadoReceta.html", ingredientes=ingredientes, nutrientes=nutrientes_totales)

# Detalle de receta: obtiene info de spoonacular y hace intento de mapear ingredientes a USDA para nutrientes
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
        # Texto original del ingrediente y consulta simplificada
        original = ing.get("originalString") or f"{ing.get('amount')} {ing.get('unit')} {ing.get('name')}"
        query_text = f"{ing.get('amount', '')} {ing.get('unit', '')} {ing.get('name', '')}".strip()

        # Estas funciones (search_foods, get_food, extract_nutrients) deben provenir de usda_api o similares
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

            # Convertir unidades comunes a gramos para escalar nutrientes
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
            # Si no se encuentra equivalente en USDA, devolver zeros
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

    # Sumar totales de la receta
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

# Rutas estáticas adicionales
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