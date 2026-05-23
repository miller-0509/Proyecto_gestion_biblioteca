import requests
from bs4 import BeautifulSoup
import sys

BASE_URL = "http://127.0.0.1:81"

# Roles to test
USERS = {
    "administrador": ("admin_sena@biblioteca.com", "AdminSena123!"),
    "bibliotecario": ("biblioteca@gmail.com", "Bibliotecario123!"),
    "almacenista": ("almacen@gmail.com", "Almacenista123!"),
    "aprendiz": ("caperamiller5@gmail.com", "Aprendiz123!")
}

# Pages to test
PAGES = {
    "Dashboard": "/dashboard",
    "Lista de Libros": "/libros/",
    "Lista de Equipos": "/equipos/",
    "Préstamos de Libros": "/prestamos-libros/lista",
    "Préstamos de Equipos": "/prestamos/lista",
    "Reportes": "/reportes/",
    "Usuarios (Admin)": "/usuarios/",
    "Sanciones": "/multas/"
}

def get_csrf_token(session, url):
    """GET a page and extract the CSRF token."""
    try:
        r = session.get(url, timeout=5)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, 'html.parser')
        token_input = soup.find('input', {'name': 'csrf_token'})
        if token_input:
            return token_input.get('value')
    except Exception as e:
        print(f"[-] Error obteniendo token CSRF: {e}")
    return None

def test_login_and_pages():
    results = {}
    print("=" * 70)
    print("  SENA - INICIANDO PRUEBAS DE SEGURIDAD Y ACCESIBILIDAD POR ROL")
    print("=" * 70)

    for role, (email, password) in USERS.items():
        print(f"\nProbando accesos para el rol: {role.upper()} ({email})")
        session = requests.Session()
        
        # 1. Obtener CSRF de la página de Login
        csrf_token = get_csrf_token(session, BASE_URL + "/")
        if not csrf_token:
            print(f"[-] ERROR: No se pudo obtener el token CSRF para {role}")
            continue

        # 2. Enviar login
        login_data = {
            "correo": email,
            "password": password,
            "csrf_token": csrf_token
        }
        try:
            r_login = session.post(BASE_URL + "/", data=login_data, allow_redirects=True, timeout=5)
        except Exception as e:
            print(f"[-] ERROR: Solicitud de login fallida para {role}: {e}")
            continue
        
        if "¡Bienvenido" not in r_login.text and "Panel Principal" not in r_login.text:
            print(f"[-] ERROR: Inicio de sesión fallido para {role}")
            continue
        print(f"[+] Login exitoso!")

        role_results = {}
        # 3. Probar cada página
        for page_name, path in PAGES.items():
            try:
                r_page = session.get(BASE_URL + path, allow_redirects=False, timeout=5)
                status = r_page.status_code
            except Exception as e:
                print(f"  * {page_name}: ERROR DE CONEXIÓN ({e})")
                role_results[page_name] = "Error de Conexión"
                continue
            
            # Si hay redirección, ver a dónde va
            if status == 302:
                redirect_target = r_page.headers.get('Location', '')
                if "login" in redirect_target:
                    accessible = "Bloqueado (Redirigido a Login)"
                elif "dashboard" in redirect_target or redirect_target == "/" or redirect_target == "":
                    accessible = "Bloqueado (Redirigido a Inicio)"
                else:
                    accessible = f"Redirigido a {redirect_target}"
            elif status == 403:
                accessible = "Bloqueado (403 Prohibido)"
            elif status == 404:
                accessible = "No encontrado (404)"
            elif status == 200:
                if "No tienes permisos" in r_page.text or "Solo el administrador" in r_page.text:
                    accessible = "Bloqueado (Mensaje de alerta en pantalla)"
                else:
                    accessible = "Permitido (200 OK)"
            else:
                accessible = f"Código de estado: {status}"

            role_results[page_name] = accessible
            print(f"  * {page_name}: {accessible}")
        
        results[role] = role_results
        
        # Cerrar sesión
        try:
            session.get(BASE_URL + "/logout", timeout=5)
        except:
            pass

    print("\n" + "=" * 70)
    print("  RESUMEN DE PRUEBAS DE SEGURIDAD (RBAC)")
    print("=" * 70)
    header = f"{'Módulo':<25} | {'Admin':<15} | {'Bibliotecario':<15} | {'Almacenista':<15} | {'Aprendiz':<15}"
    print(header)
    print("-" * len(header))
    for page_name in PAGES.keys():
        row = f"{page_name:<25}"
        for role in ["administrador", "bibliotecario", "almacenista", "aprendiz"]:
            val = results.get(role, {}).get(page_name, "N/A")
            if "Permitido" in val:
                status_str = "PERMITIDO"
            elif "Bloqueado" in val:
                status_str = "BLOQUEADO"
            else:
                status_str = "OTRO"
            row += f" | {status_str:<15}"
        print(row)
    print("=" * 70)

if __name__ == "__main__":
    test_login_and_pages()
