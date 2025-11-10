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


if __name__ == '__main__':
    app.run(debug=True)
