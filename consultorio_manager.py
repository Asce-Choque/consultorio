import os

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def conectar():
    """Conecta a la base PostgreSQL configurada en el entorno."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL es obligatoria; configure la conexión de Supabase.")
    return psycopg2.connect(DATABASE_URL)


def consultar(query, parametros=(), uno=False):
    conn = conectar()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, parametros)
            if uno:
                row = cursor.fetchone()
                return dict(row) if row else None
            return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def ejecutar(query, parametros=()):
    conn = conectar()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, parametros)
            filas_afectadas = cursor.rowcount
        conn.commit()
        return filas_afectadas
    finally:
        conn.close()


def listar_pacientes():
    """Muestra todos los pacientes registrados."""
    return consultar(
        "SELECT dni, nombre, apellido, telefono FROM pacientes ORDER BY apellido, nombre"
    )


def listar_atenciones():
    """Muestra todas las atenciones registradas con la fecha y el DNI."""
    return consultar(
        """
        SELECT a.id_atencion, a.dni_paciente, p.nombre, p.apellido, a.fecha_atencion
        FROM atenciones a
        JOIN pacientes p ON p.dni = a.dni_paciente
        ORDER BY a.fecha_atencion DESC
        """
    )


def buscar_paciente_por_dni(dni):
    """Busca un paciente por DNI y devuelve su registro."""
    return consultar(
        "SELECT dni, nombre, apellido, telefono FROM pacientes WHERE dni = %s",
        (dni,),
        uno=True,
    )


def eliminar_atencion(id_atencion):
    """Elimina una atención por su ID."""
    return ejecutar("DELETE FROM atenciones WHERE id_atencion = %s", (id_atencion,))


def eliminar_paciente(dni):
    """Elimina un paciente y sus atenciones asociadas."""
    return ejecutar("DELETE FROM pacientes WHERE dni = %s", (dni,))


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
