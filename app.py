from flask import Flask, render_template, request, redirect, url_for, flash, session

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
    usuario = cazadores.get(email, {})
    registro = usuario.get('profile', {})  

    return render_template('perfil.html', usuario=usuario, registro=registro)

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
            flash('usuario no encontrado', 'error')

    return render_template('iniciar.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    total_steps = 17
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
            email = registro.get('email')
            nombre = registro.get('nombre', 'Usuario')
            password = registro.get('password', '')
            if not email:
                flash('Faltan email o contraseña en los datos de registro.', 'error')
                return redirect(url_for('registro', step=1))
            if email in cazadores:
                flash('Ya existe una cuenta con ese correo.', 'error')
                return redirect(url_for('registro', step=1))

            cazadores[email] = {
                'password': password,
                'nombre': nombre,
                'profile': registro.copy()
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
                # Fórmula de Devine: base 50/45.5 + 2.3 * (inches - 60)
                if sexo == 'Male':
                    pmi = 50.0 + 2.3 * (altura_in - 60.0)
                elif sexo == 'Female':
                    pmi = 45.5 + 2.3 * (altura_in - 60.0)
        except ValueError:
            pmi = None
    return render_template('calculadora_PMI.html', pmi=pmi, sexo=sexo, altura=altura)

if __name__ == '__main__':
    app.run(debug=True)
