from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, g, jsonify, render_template, request

ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "consultorio.db")

app = Flask(__name__)


def connect_db():
    """Crea la conexión SQLite y activa el soporte de claves foráneas."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_db():
    """Mantiene una conexión por request para reutilizarla en la app."""
    if "db" not in g:
        g.db = connect_db()
    return g.db


@app.teardown_appcontext
def close_db(_exception):
    """Cierra la conexión al finalizar cada request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea las tablas necesarias si aún no existen."""
    db = connect_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS pacientes (
            dni TEXT PRIMARY KEY,
            nombre TEXT,
            apellido TEXT,
            telefono TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS atenciones (
            id_atencion INTEGER PRIMARY KEY AUTOINCREMENT,
            dni_paciente TEXT,
            fecha_atencion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dni_paciente) REFERENCES pacientes(dni)
        )
        """
    )
    db.commit()
    db.close()


@app.route("/")
def index():
    """Renderiza la pantalla principal de la aplicación."""
    return render_template("index.html")


@app.route("/api/buscar/<dni>", methods=["GET"])
def buscar_paciente(dni):
    """Busca un paciente por DNI. Devuelve el registro o un estado de no encontrado."""
    db = get_db()
    paciente = db.execute(
        "SELECT dni, nombre, apellido, telefono FROM pacientes WHERE dni = ?",
        (dni,),
    ).fetchone()

    if paciente is None:
        return jsonify({"encontrado": False, "mensaje": "Paciente no registrado."})

    return jsonify({"encontrado": True, "paciente": dict(paciente)})


@app.route("/api/atencion", methods=["POST"])
def registrar_atencion():
    """Registra una atención: crea un paciente si hace falta y luego guarda la atención."""
    payload = request.get_json(silent=True) or {}
    dni = (payload.get("dni") or "").strip()

    if not dni:
        return jsonify({"ok": False, "mensaje": "El DNI es obligatorio."}), 400

    db = get_db()
    paciente = db.execute(
        "SELECT dni, nombre, apellido, telefono FROM pacientes WHERE dni = ?",
        (dni,),
    ).fetchone()

    if paciente is None:
        nombre = (payload.get("nombre") or "").strip()
        apellido = (payload.get("apellido") or "").strip()
        telefono = (payload.get("telefono") or "").strip()

        if not nombre or not apellido:
            return jsonify(
                {
                    "ok": False,
                    "mensaje": "Para dar de alta un paciente nuevo, se requieren nombre y apellido.",
                }
            ), 400

        db.execute(
            "INSERT INTO pacientes (dni, nombre, apellido, telefono) VALUES (?, ?, ?, ?)",
            (dni, nombre, apellido, telefono),
        )
        paciente = {"dni": dni, "nombre": nombre, "apellido": apellido, "telefono": telefono}

    ahora = datetime.now(ARGENTINA_TZ)
    fecha = ahora.strftime("%Y-%m-%d %H:%M:%S")
    db.execute("INSERT INTO atenciones (dni_paciente, fecha_atencion) VALUES (?, ?)", (dni, fecha))
    db.commit()

    hora = ahora.strftime("%H:%M")
    nombre_completo = f"{paciente['nombre']} {paciente['apellido']}".strip()
    return jsonify(
        {
            "ok": True,
            "mensaje": f"Atención registrada para {nombre_completo} - {hora}",
            "paciente": {"dni": dni, "nombre": paciente["nombre"], "apellido": paciente["apellido"]},
            "hora": hora,
        }
    )


@app.route("/api/atenciones-hoy", methods=["GET"])
def atenciones_hoy():
    """Devuelve todas las atenciones del día actual en la zona horaria de Argentina."""
    db = get_db()
    fecha_hoy = datetime.now(ARGENTINA_TZ).date().isoformat()
    filas = db.execute(
        """
        SELECT a.id_atencion, a.dni_paciente, p.nombre, p.apellido, a.fecha_atencion
        FROM atenciones a
        JOIN pacientes p ON p.dni = a.dni_paciente
        WHERE date(a.fecha_atencion) = ?
        ORDER BY a.fecha_atencion DESC
        """,
        (fecha_hoy,),
    ).fetchall()

    resultados = []
    for fila in filas:
        hora = datetime.strptime(fila["fecha_atencion"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        resultados.append(
            {
                "id_atencion": fila["id_atencion"],
                "dni": fila["dni_paciente"],
                "nombre": fila["nombre"],
                "apellido": fila["apellido"],
                "hora": hora,
            }
        )

    return jsonify({"atenciones": resultados})


@app.route("/api/atencion/<int:id_atencion>", methods=["DELETE"])
def eliminar_atencion(id_atencion):
    """Elimina una atención del historial dejando intacto el paciente registrado."""
    db = get_db()
    fila = db.execute(
        "SELECT id_atencion FROM atenciones WHERE id_atencion = ?",
        (id_atencion,),
    ).fetchone()

    if fila is None:
        return jsonify({"ok": False, "mensaje": "La atención no existe."}), 404

    db.execute("DELETE FROM atenciones WHERE id_atencion = ?", (id_atencion,))
    db.commit()
    return jsonify({"ok": True, "mensaje": "Atención eliminada del historial."})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
