from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'theswordoftarnished'

cazadores = {
    'correo@gmail.com': {
        'password': '1234',
        'nombre': 'administrador',
    }
}

def safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def calcular_imc(peso_kg, altura_cm):
    w = safe_float(peso_kg)
    h = safe_float(altura_cm)
    if w and h and h > 0:
        h_m = h / 100.0
        return round(w / (h_m * h_m), 1)
    return None

def calcular_tmb_mifflin(sexo, peso_kg, altura_cm, edad):
    w = safe_float(peso_kg); h = safe_float(altura_cm); a = safe_float(edad)
    if None in (w, h, a) or sexo not in ('male', 'female'):
        return None
    s = 5 if sexo == 'male' else -161
    tmb = 10 * w + 6.25 * h - 5 * a + s
    return int(round(tmb))

def actividad_multiplier(text):
    if not text:
        return 1.2
    t = str(text).lower()
    if 'baja' in t or 'sedent' in t:
        return 1.2
    if 'lig' in t or 'light' in t:
        return 1.375
    if 'mod' in t or 'moderada' in t:
        return 1.55
    if 'alta' in t or 'active' in t:
        return 1.725
    if 'muy' in t or 'very' in t:
        return 1.9
    return 1.2

def calcular_tdee(tmb, actividad_text):
    if tmb is None:
        return None
    m = actividad_multiplier(actividad_text)
    return int(round(tmb * m))

def peso_ideal_devine(sexo, altura_cm):
    h = safe_float(altura_cm)
    if not h:
        return None
    inches = h / 2.54
    base = 50.0 if sexo == 'male' else 45.5
    ideal = base + 2.3 * (inches - 60) if inches > 60 else base
    return round(ideal, 1)

def calcular_macros(calorias, objetivo=None, peso_kg=None):
    if not calorias:
        return None
    if objetivo == 'bajar':
        split = {'carbs': 0.45, 'protein': 0.30, 'fat': 0.25}
    elif objetivo == 'aumentar':
        split = {'carbs': 0.50, 'protein': 0.25, 'fat': 0.25}
    else:
        split = {'carbs': 0.50, 'protein': 0.20, 'fat': 0.30}
    carbs_kcal = calorias * split['carbs']
    protein_kcal = calorias * split['protein']
    fat_kcal = calorias * split['fat']
    protein_g = round(protein_kcal / 4)
    carbs_g = round(carbs_kcal / 4)
    fat_g = round(fat_kcal / 9)
    protein_per_kg = None
    ppk = safe_float(protein_g) and safe_float(peso_kg) and round(protein_g / safe_float(peso_kg), 2) if peso_kg else None
    if ppk:
        protein_per_kg = ppk
    return {
        'kcal': int(round(calorias)),
        'carbs_g': carbs_g,
        'protein_g': protein_g,
        'fat_g': fat_g,
        'protein_per_kg': protein_per_kg,
        'split': split
    }

@app.route('/')
def home():
    if not session.get('logueado') and not session.get('seen_welcome'):
        session['seen_welcome'] = True
        return render_template('welcome.html')

    tools = None
    if session.get('logueado'):
        email = session.get('usuario_email')
        usuario = cazadores.get(email, {})
        profile = usuario.get('profile') or {}
        peso = profile.get('peso') or profile.get('weight')
        altura = profile.get('altura') or profile.get('height')
        edad = profile.get('edad') or profile.get('age')
        sexo = profile.get('sexo') or profile.get('gender')
        actividad = profile.get('actividad')

        imc = calcular_imc(peso, altura)
        tmb = calcular_tmb_mifflin(sexo, peso, altura, edad)
        tdee = calcular_tdee(tmb, actividad)
        ideal = peso_ideal_devine(sexo, altura)
        macros = calcular_macros(tdee, objetivo=profile.get('objetivo'), peso_kg=peso)

        tools = {
            'imc': imc,
            'tmb': tmb,
            'tdee': tdee,
            'peso_ideal': ideal,
            'macros': macros,
            'profile': profile
        }

    return render_template('inicio.html', tools=tools)

@app.route('/iniciar', methods=['GET', 'POST'])
def iniciar():
    if session.get('logueado'):
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Que el cazador ingrese su correo y contraseña', 'error')
        elif email in cazadores:
            usuario = cazadores[email]
            if usuario['password'] == password:
                session['usuario_email'] = email
                session['cazador'] = usuario['nombre']
                session['logueado'] = True
                flash(f"El cazador {usuario['nombre']} ha despertado nuevamente...", "success")
                return redirect(url_for('home'))
            else:
                flash('Contraseña equivocada', 'error')
        else:
            flash('Cazador no encontrado', 'error')

    return render_template('iniciar.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    # ahora: paso 1 = email+password, luego preguntas una por página, último paso revisión
    total_steps = 17
    try:
        step = int(request.args.get('step', 1))
    except ValueError:
        step = 1

    registro = session.get('registro', {})

    if request.method == 'POST':
        # paso 1: email + password
        if step == 1:
            registro['email'] = request.form.get('email', '').strip()
            registro['password'] = request.form.get('password', '')
        elif step == 2:
            registro['nombre'] = request.form.get('nombre', '').strip()
        elif step == 3:
            registro['apellido'] = request.form.get('apellido', '').strip()
        elif step == 4:
            registro['edad'] = request.form.get('edad', '').strip()
        elif step == 5:
            registro['sexo'] = request.form.get('sexo', '').strip()
        elif step == 6:
            registro['peso'] = request.form.get('peso', '').strip()
        elif step == 7:
            registro['altura'] = request.form.get('altura', '').strip()
        elif step == 8:
            registro['actividad'] = request.form.get('actividad', '').strip()
        elif step == 9:
            registro['objetivo'] = request.form.get('objetivo', '').strip()
        elif step == 10:
            registro['alergias'] = request.form.get('alergias', '').strip()
        elif step == 11:
            registro['intolerancias'] = request.form.get('intolerancias', '').strip()
        elif step == 12:
            registro['dieta'] = request.form.get('dieta', '').strip()
        elif step == 13:
            registro['alimentos_no_gustan'] = request.form.get('alimentos_no_gustan', '').strip()
        elif step == 14:
            registro['experiencia_cocina'] = request.form.get('experiencia_cocina', '').strip()
        elif step == 15:
            registro['condiciones_medicas'] = request.form.get('condiciones_medicas', '').strip()
        elif step == 16:
            # opción: acumular calorías no alcanzadas al día siguiente
            registro['acumular_calorias'] = request.form.get('acumular_calorias', 'no')
        session['registro'] = registro

        # Si no es último paso, avanzar
        if step < total_steps:
            return redirect(url_for('registro', step=step + 1))

        # paso final (17): revisar -> action agregar/omitir
        action = request.form.get('action')
        if action == 'agregar':
            email = registro.get('email')
            nombre = registro.get('nombre', 'Usuario')
            password = registro.get('password', '')
            if not email or not password:
                flash('Faltan email o contraseña en los datos de registro.', 'error')
                return redirect(url_for('registro', step=1))
            if email in cazadores:
                flash('Ya existe una cuenta con ese correo.', 'error')
                return redirect(url_for('registro', step=1))
            cazadores[email] = {'password': password, 'nombre': nombre, 'profile': registro}
            session['usuario_email'] = email
            session['cazador'] = nombre
            session['logueado'] = True
            session.pop('registro', None)
            flash(f"Cuenta creada. Bienvenido {nombre}.", 'success')
            return redirect(url_for('home'))
        else:
            session.pop('registro', None)
            flash('Registro omitido. Puedes completar el perfil más tarde.', 'info')
            return redirect(url_for('home'))

    # GET -> mostrar plantilla del paso solicitado
    return render_template('registro.html', step=step, total_steps=total_steps, registro=registro)


@app.route('/cerrar')
def cerrar():
    session.clear()
    flash("El cazador ha regresado a su sueño...", "danger")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
