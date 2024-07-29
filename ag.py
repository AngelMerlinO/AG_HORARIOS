import random
import numpy as np
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import math

from data import mapa_curricular

app = Flask(__name__)
CORS(app)

class Materia:
    def __init__(self, nombre, cuatrimestre, grupo, lunes, martes, miercoles, jueves, viernes):
        self.nombre = nombre
        self.cuatrimestre = cuatrimestre
        self.grupo = grupo
        self.calif_cuatrimestre = None
        self.calif_seriacion = None
        self.calif_holgura = None
        self.lunes = lunes
        self.martes = martes
        self.miercoles = miercoles
        self.jueves = jueves
        self.viernes = viernes

    def __eq__(self, other):
        if isinstance(other, Materia):
            return (self.nombre == other.nombre and self.cuatrimestre == other.cuatrimestre and
                    self.grupo == other.grupo and self.lunes == other.lunes and
                    self.martes == other.martes and self.miercoles == other.miercoles and
                    self.jueves == other.jueves and self.viernes == other.viernes)
        return False

    def __hash__(self):
        return hash((self.nombre, self.cuatrimestre, self.grupo, tuple(self.lunes), tuple(self.martes), tuple(self.miercoles), tuple(self.jueves), tuple(self.viernes)))

    def asignar_calif_cuatrimestre(self, calif):
        self.calif_cuatrimestre = calif

    def asignar_calif_seriacion(self, calif):
        self.calif_seriacion = calif

    def asignar_calif_holgura(self, calif):
        self.calif_holgura = calif

class AlgoritmoGenetico:
    def __init__(self, prob_cruza, prob_mutacion, pob_maxima, pob_inicial, generaciones, materias):
        self.prob_cruza = prob_cruza 
        self.prob_mutacion = prob_mutacion
        self.pob_inicial = pob_inicial
        self.pob_maxima = pob_maxima
        self.materias = materias
        self.generaciones = generaciones
        self.poblacion = []
        self.maximo_de_materias = 9
        self.calif_cuatrimestre_meta = None
        self.calif_seriacion_meta = None
        self.calif_holgura_meta = None
        self.resultados = []

    def crear_pob_inicial(self):
        for i in range(self.pob_inicial):
            horario = set()
            limite = None
            numero_materias_distintas = self.numero_materias_nombre_distinto()
            if numero_materias_distintas < self.maximo_de_materias: 
                limite = random.randint((numero_materias_distintas//2) + 1, numero_materias_distintas) 
            else:
                limite = random.randint((self.maximo_de_materias//2) + 1, self.maximo_de_materias)
            conta_0 = 0
            while conta_0 < limite: 
                materia = None
                indices = []
                bandera = True
                while not materia or self.evaluar_materias_mismo_nombre(materia,horario) or self.evaluar_choque_materias(materia, horario):
                    if len(indices) == len(self.materias):
                        bandera = False
                        break
                    indice_random = random.randint(0,len(self.materias)-1)
                    while indice_random in indices:
                        indice_random = random.randint(0,len(self.materias)-1)
                    indices.append(indice_random)
                    materia = self.materias[indice_random]
                if bandera:
                    horario.add(materia)
                conta_0 += 1
            self.poblacion.append(horario)
        
    def evaluar_choque_materias(self,materia, horario):
        cont = 0
        for elemento in horario:
            for dia in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']:
                horas_dia_materia_horario = set(getattr(elemento, dia))
                horas_dia_materia = set(getattr(materia, dia))
                cont += len(horas_dia_materia_horario.intersection(horas_dia_materia))
        if cont == 0:
            return False
        else:
            return True

    
    def evaluar_materias_mismo_nombre(self,materia, horario):
        for elemento in horario:
            if materia.nombre == elemento.nombre:
                return True
        return False
    
    def numero_materias_nombre_distinto(self):
        nombres_unicos = set()
        for materia in self.materias:
            nombres_unicos.add(materia.nombre)
        return len(nombres_unicos)
    
    def obtener_media_calif_cuatri(self):
        suma = 0
        for materia in self.materias:
            suma += materia.calif_cuatrimestre
        media = suma/len(self.materias)
        self.calif_cuatrimestre_meta = media*self.maximo_de_materias

    def obtener_max_calif_seriacion(self):
        mayor_calif_seriacion = self.materias[0].calif_seriacion
        for materia in self.materias:
            if materia.calif_seriacion > mayor_calif_seriacion:
                mayor_calif_seriacion = materia.calif_seriacion
        self.calif_seriacion_meta = mayor_calif_seriacion*self.maximo_de_materias
    
    def obtener_media_calif_holgura(self):
        suma = 0
        n = len(self.materias)
        for materia in self.materias:
            suma += materia.calif_holgura
        media = suma / n
        suma_diferencias_cuadradas = sum((materia.calif_holgura - media) ** 2 for materia in self.materias)
        desviacion_estandar = math.sqrt(suma_diferencias_cuadradas / (n-1))
        self.calif_holgura_meta = media - (1/2)*desviacion_estandar

    def emparejar(self):
        probas_cruza = []
        hijos = []
        for _ in self.poblacion:
            probas_cruza.append(random.random())
        for i in range(len(self.poblacion)):
            if probas_cruza[i] < self.prob_cruza:
                hijos = self.reproducir(self.poblacion[i],self.poblacion[random.randint(0,len(self.poblacion)-1)])
                self.poblacion.extend(hijos)

    def reproducir(self,padre, madre):
        hijos = None
        hijo_1 = set()
        hijo_2 = set()
        interseccion = padre.intersection(madre)
        hijo_1.update(interseccion)
        hijo_2.update(interseccion)
        union = padre.union(madre)
        dif = union.difference(interseccion)
        cont = 0
        for materia in dif:
            if cont%2 == 0:
                if not self.evaluar_materias_mismo_nombre(materia, hijo_1) and not self.evaluar_choque_materias(materia,hijo_1) and len(hijo_1) < self.maximo_de_materias:
                    hijo_1.add(materia)
                elif not self.evaluar_materias_mismo_nombre(materia, hijo_2) and not self.evaluar_choque_materias(materia,hijo_2) and len(hijo_2) < self.maximo_de_materias:
                    hijo_2.add(materia)
            else:
                if not self.evaluar_materias_mismo_nombre(materia, hijo_2) and not self.evaluar_choque_materias(materia,hijo_2) and len(hijo_2) < self.maximo_de_materias:
                    hijo_2.add(materia)
                elif not self.evaluar_materias_mismo_nombre(materia, hijo_1) and not self.evaluar_choque_materias(materia,hijo_1) and len(hijo_1) < self.maximo_de_materias:
                    hijo_1.add(materia)
            cont += 1  
        hijos = [hijo_1,hijo_2]
        return self.mutar(hijos)
    
    def mutar(self, hijos):
        for hijo in hijos:
            proba_mute = random.random()
            if proba_mute <= self.prob_mutacion:
                quitar_agregar = random.random()
                if quitar_agregar < 0.5 and len(hijo)>1:
                    hijo.pop()
                else:
                    if len(hijo) < self.maximo_de_materias:
                        materia = None
                        indices = []
                        bandera = True
                        while not materia or self.evaluar_materias_mismo_nombre(materia,hijo) or self.evaluar_choque_materias(materia, hijo):
                            if len(indices) == len(self.materias):
                                bandera = False
                                break
                            indice_random = random.randint(0,len(self.materias)-1)
                            while indice_random in indices:
                                indice_random = random.randint(0,len(self.materias)-1)
                            indices.append(indice_random)
                            materia = self.materias[indice_random]
                        if bandera:
                            hijo.add(materia)
        return(hijos)
    
    def evaluar_poblacion(self):
        aptitudes = []
        ys_calculadas = []
        for individuo in self.poblacion:
            cont_calif_cuatri = 0
            cont_calif_seriacion = 0
            cont_calif_holgura = 0
            for materia in individuo:
                cont_calif_cuatri += materia.calif_cuatrimestre
                cont_calif_seriacion += materia.calif_seriacion
                cont_calif_holgura += materia.calif_holgura
            yc = [
                len(individuo),
                cont_calif_cuatri, 
                cont_calif_seriacion, 
                cont_calif_holgura
            ]
            ys_calculadas.append(np.array(yc))
        yd = np.array([self.maximo_de_materias, self.calif_cuatrimestre_meta, self.calif_seriacion_meta, self.calif_holgura_meta])
        for i in range(len(self.poblacion)):
            yd_aux = yd.tolist()
            yd_aux[3] = yd_aux[3]*ys_calculadas[i][0]
            yd_aux = np.array(yd_aux)
            error = yd_aux - ys_calculadas[i]
            norma = np.linalg.norm(error)
            aptitudes.append((norma, i))
        aptitudes.sort(key=lambda x: x[0])
        return aptitudes

    def podar(self):
        poblacion_sin_duplicados = set()
        for individuo in self.poblacion:
            individuo_canonico = tuple(sorted(individuo, key=lambda x: (x.nombre, x.cuatrimestre, x.grupo)))
            poblacion_sin_duplicados.add(individuo_canonico)
        self.poblacion = [set(individuo) for individuo in poblacion_sin_duplicados]
        aptitudes = self.evaluar_poblacion()
        poblacion_podada = []
        for i in range(len(self.poblacion)):
            poblacion_podada.append(self.poblacion[aptitudes[i][1]])
        if len(self.poblacion) > self.pob_maxima:
            poblacion_podada = poblacion_podada[:self.pob_maxima]    
        self.poblacion = poblacion_podada
    
    def main(self):
        self.obtener_media_calif_cuatri()
        self.obtener_max_calif_seriacion()
        self.obtener_media_calif_holgura()
        self.crear_pob_inicial()
        for i in range(self.generaciones):
            self.emparejar()
            self.podar()
        self.resultados = [
            [{k: getattr(elemento, k) for k in vars(elemento)} for elemento in individuo]
            for individuo in self.poblacion
        ]

def obtener_calif_cuatrimestre(materias):
    cuatris = set()
    for materia in materias:
        cuatris.add(materia.cuatrimestre)
    cuatris = list(cuatris)
    cuatris.sort(reverse=True)
    for materia in materias:
        materia.asignar_calif_cuatrimestre(cuatris.index(materia.cuatrimestre) + 1)

def obtener_calif_seriacion(materias):
    for materia in materias:
        calif = 0
        for asignatura in mapa_curricular:
            if materia.nombre == asignatura['nombre']:
                lista_aux = list(reversed(asignatura['seriacion']))
                for i in range(len(lista_aux)):
                    if lista_aux[i]:
                        calif += lista_aux[i] * (i + 1)
                materia.asignar_calif_seriacion(calif)
                break

def obtener_calif_holgura(materias, cuatrimestre_alumno):
    for materia in materias:
        for asignatura in mapa_curricular:
            if materia.nombre == asignatura['nombre']:
                if asignatura['cuatrimestre'] + asignatura['holgura'] <= cuatrimestre_alumno:
                    materia.asignar_calif_holgura(0)
                else:
                    materia.asignar_calif_holgura(asignatura['cuatrimestre'] + asignatura['holgura'] - cuatrimestre_alumno)
                break

def materias_from_json(json_data):
    materias_list = []
    for item in json_data:
        materias_list.append(Materia(
            nombre=item['nombre'],
            cuatrimestre=item['cuatrimestre'],
            grupo=item['grupo'],
            lunes=item['lunes'],
            martes=item['martes'],
            miercoles=item['miercoles'],
            jueves=item['jueves'],
            viernes=item['viernes']
        ))
    return materias_list

@app.route('/genetico', methods=['POST'])
def ejecutar_algoritmo_genetico():
    json_data = request.get_json()
    cuatrimestre_alumno = json_data['cuatrimestre_alumno']
    materias = materias_from_json(json_data['materias'])
    
    obtener_calif_cuatrimestre(materias)
    obtener_calif_seriacion(materias)
    obtener_calif_holgura(materias, cuatrimestre_alumno)
    
    ag = AlgoritmoGenetico(0.8, 0.8, 10, 100, 500, materias)
    ag.main()
    
    if ag.resultados:
        return jsonify(ag.resultados[0])
    else:
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
