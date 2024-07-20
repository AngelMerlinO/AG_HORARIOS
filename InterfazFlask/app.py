from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os

app = Flask(__name__)

class Materia:
    def __init__(self, nombre, cuatrimestre, grupo, lunes, martes, miercoles, jueves, viernes):
        self.nombre = nombre
        self.cuatrimestre = cuatrimestre
        self.grupo = grupo
        self.horarios = {
            'lunes': lunes,
            'martes': martes,
            'miercoles': miercoles,
            'jueves': jueves,
            'viernes': viernes
        }

data_path = os.path.join(os.path.dirname(__file__), '../data.py')
data = {}
exec(open(data_path).read(), data)

mapa_curricular = data['mapa_curricular']

selected_materias = []

cuatrimestre_alumno = None

@app.route('/', methods=['GET', 'POST'])
def index():
    global cuatrimestre_alumno
    if request.method == 'POST':
        cuatrimestre_alumno = int(request.form['cuatrimestre_alumno'])
        return redirect(url_for('materias'))

    return render_template('cuatrimestre.html')

@app.route('/materias', methods=['GET', 'POST'])
def materias():
    global cuatrimestre_alumno
    if cuatrimestre_alumno is None:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        materia_nombre = request.form['materia']
        grupo = request.form['grupo'].upper()
        horarios = {
            'lunes': [int(h) for h in request.form.getlist('lunes')[0].split(',') if h],
            'martes': [int(h) for h in request.form.getlist('martes')[0].split(',') if h],
            'miercoles': [int(h) for h in request.form.getlist('miercoles')[0].split(',') if h],
            'jueves': [int(h) for h in request.form.getlist('jueves')[0].split(',') if h],
            'viernes': [int(h) for h in request.form.getlist('viernes')[0].split(',') if h]
        }

        cuatrimestre_materia = next((m['cuatrimestre'] for m in mapa_curricular if m['nombre'] == materia_nombre), None)
        if cuatrimestre_materia is None:
            return "La materia seleccionada no existe en el mapa curricular."

        selected_materia = f"{materia_nombre} - {grupo}"
        
        if selected_materia not in [f"{m.nombre} - {m.grupo}" for m in selected_materias]:
            new_materia = Materia(materia_nombre, cuatrimestre_materia, grupo, horarios['lunes'], horarios['martes'], horarios['miercoles'], horarios['jueves'], horarios['viernes'])
            selected_materias.append(new_materia)
        else:
            return "La materia ya ha sido seleccionada."
        
        return redirect(url_for('materias'))

    json_data = {
        'cuatrimestre_alumno': cuatrimestre_alumno,
        'materias': [{
            'nombre': materia.nombre,
            'cuatrimestre': materia.cuatrimestre,
            'grupo': materia.grupo,
            'lunes': materia.horarios['lunes'],
            'martes': materia.horarios['martes'],
            'miercoles': materia.horarios['miercoles'],
            'jueves': materia.horarios['jueves'],
            'viernes': materia.horarios['viernes']
        } for materia in selected_materias]
    }

    json_string = json.dumps(json_data, default=str)

    return render_template('index.html', cuatrimestre_alumno=cuatrimestre_alumno, mapa_curricular=mapa_curricular, selected_materias=selected_materias, materias_json=json_string)

if __name__ == '__main__':
    app.run(debug=True)
