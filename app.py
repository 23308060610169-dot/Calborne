from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'theswordoftarnished'

cazadores = {
    'correo@gmail.com': {
        'password': '1234',
        'nombre': 'administrador',
    }
}


@app.route('/')
def home():
    if not session.get('logueado') and not session.get('seen_welcome'):
        session['seen_welcome'] = True
        return render_template('welcome.html')

    if session.get('logueado'):
        email = session.get('usuario_email')
        usuario = cazadores.get(email, {})
        profile = usuario.get('profile') or {}
        peso = profile.get('peso') or profile.get('weight')
        altura = profile.get('altura') or profile.get('height')
        edad = profile.get('edad') or profile.get('age')
        sexo = profile.get('sexo') or profile.get('gender')
        actividad = profile.get('actividad')


    return render_template('inicio.html')

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
            registro['acumular_calorias'] = request.form.get('acumular_calorias', 'no')
        session['registro'] = registro

        if step < total_steps:
            return redirect(url_for('registro', step=step + 1))

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

    return render_template('registro.html', step=step, total_steps=total_steps, registro=registro)


@app.route('/cerrar')
def cerrar():
    session.clear()
    flash("El cazador ha regresado a su sueño...", "danger")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
