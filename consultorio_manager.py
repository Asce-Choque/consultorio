import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "consultorio.db"


def conectar():
    """Conecta con la base de datos y activa claves foráneas."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def listar_pacientes():
    """Muestra todos los pacientes registrados."""
    conn = conectar()
    rows = conn.execute(
        "SELECT dni, nombre, apellido, telefono FROM pacientes ORDER BY apellido, nombre"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def listar_atenciones():
    """Muestra todas las atenciones registradas con la fecha y el DNI."""
    conn = conectar()
    rows = conn.execute(
        """
        SELECT a.id_atencion, a.dni_paciente, p.nombre, p.apellido, a.fecha_atencion
        FROM atenciones a
        JOIN pacientes p ON p.dni = a.dni_paciente
        ORDER BY a.fecha_atencion DESC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def buscar_paciente_por_dni(dni):
    """Busca un paciente por DNI y devuelve su registro."""
    conn = conectar()
    row = conn.execute(
        "SELECT dni, nombre, apellido, telefono FROM pacientes WHERE dni = ?",
        (dni,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def eliminar_atencion(id_atencion):
    """Elimina una atención por su ID."""
    conn = conectar()
    cursor = conn.execute("DELETE FROM atenciones WHERE id_atencion = ?", (id_atencion,))
    conn.commit()
    conn.close()
    return cursor.rowcount


def eliminar_paciente(dni):
    """Elimina un paciente y sus atenciones asociadas."""
    conn = conectar()
    cursor = conn.execute("DELETE FROM pacientes WHERE dni = ?", (dni,))
    conn.commit()
    conn.close()
    return cursor.rowcount


def menu():
    """Menú simple para consultar y eliminar registros manualmente."""
    while True:
        print("\n=== Consultorio Manager ===")
        print("1) Ver pacientes")
        print("2) Ver atenciones")
        print("3) Buscar paciente por DNI")
        print("4) Eliminar atención por ID")
        print("5) Eliminar paciente por DNI")
        print("6) Salir")

        opcion = input("Seleccioná una opción: ").strip()

        if opcion == "1":
            pacientes = listar_pacientes()
            if not pacientes:
                print("No hay pacientes registrados.")
                continue
            for paciente in pacientes:
                print(paciente)

        elif opcion == "2":
            atenciones = listar_atenciones()
            if not atenciones:
                print("No hay atenciones registradas.")
                continue
            for atencion in atenciones:
                print(atencion)

        elif opcion == "3":
            dni = input("Ingresá el DNI: ").strip()
            paciente = buscar_paciente_por_dni(dni)
            print(paciente if paciente else "No se encontró el paciente.")

        elif opcion == "4":
            id_atencion = input("Ingresá el ID de la atención a eliminar: ").strip()
            try:
                id_atencion = int(id_atencion)
            except ValueError:
                print("ID inválido.")
                continue
            filas = eliminar_atencion(id_atencion)
            print(f"Atenciones eliminadas: {filas}")

        elif opcion == "5":
            dni = input("Ingresá el DNI del paciente a eliminar: ").strip()
            filas = eliminar_paciente(dni)
            print(f"Pacientes eliminados: {filas}")

        elif opcion == "6":
            print("Saliendo...")
            break

        else:
            print("Opción inválida.")


if __name__ == "__main__":
    menu()
