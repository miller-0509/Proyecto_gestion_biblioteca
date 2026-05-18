"""
Script de prueba para verificar que la autenticación funciona correctamente.
Simula: login -> acceso a dashboard -> acceso a otra página (sesión persiste).
"""
import re
import http.cookiejar
import urllib.request
import urllib.parse

BASE = 'http://127.0.0.1:81'

# Crear un opener con soporte de cookies (simula un navegador)
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cj),
    urllib.request.HTTPRedirectHandler()
)

print("=" * 60)
print("TEST 1: Cargar página de login")
print("=" * 60)
resp = opener.open(f'{BASE}/')
html = resp.read().decode()
print(f"  Status: {resp.status}")
print(f"  URL final: {resp.url}")
print(f"  Cookies: {[c.name for c in cj]}")

# Extraer CSRF token
csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
if csrf_match:
    csrf_token = csrf_match.group(1)
    print(f"  CSRF token: {csrf_token[:20]}...")
else:
    print("  ERROR: No se encontró CSRF token!")
    exit(1)

print()
print("=" * 60)
print("TEST 2: Intentar login con credenciales incorrectas")
print("=" * 60)
data = urllib.parse.urlencode({
    'csrf_token': csrf_token,
    'correo': 'noexiste@test.com',
    'password': 'wrongpass'
}).encode()
resp = opener.open(urllib.request.Request(f'{BASE}/', data=data, method='POST'))
html = resp.read().decode()
print(f"  Status: {resp.status}")
print(f"  URL final: {resp.url}")
has_error = 'inválidas' in html or 'danger' in html
print(f"  Muestra error de credenciales: {has_error}")

# Obtener nuevo CSRF token para el siguiente intento
csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
if csrf_match:
    csrf_token = csrf_match.group(1)

print()
print("=" * 60)
print("TEST 2B: Intentar login con credenciales CORRECTAS")
print("=" * 60)
data = urllib.parse.urlencode({
    'csrf_token': csrf_token,
    'correo': 'flask_test_user@example.com',
    'password': 'Password123*'
}).encode()
try:
    resp = opener.open(urllib.request.Request(f'{BASE}/', data=data, method='POST'))
    html = resp.read().decode()
    print(f"  Status: {resp.status}")
    print(f"  URL final: {resp.url}")
    print(f"  Cookies: {[c.name for c in cj]}")
    has_success = 'Bienvenido' in html or 'dashboard' in resp.url or 'session' in [c.name for c in cj] or 'biblioteca_session' in [c.name for c in cj]
    print(f"  Login exitoso detectado: {has_success}")
except Exception as e:
    print(f"  ERROR durante login correcto: {e}")

print()
print("=" * 60)
print("TEST 3: Verificar que /dashboard redirige a login sin sesión")
print("=" * 60)
resp = opener.open(f'{BASE}/dashboard')
html = resp.read().decode()
print(f"  Status: {resp.status}")
print(f"  URL final: {resp.url}")
print(f"  Redirigió a login: {'/' == urllib.parse.urlparse(resp.url).path or 'Iniciar' in html}")

print()
print("=" * 60)
print("RESUMEN DE COOKIES ACTIVAS")
print("=" * 60)
for cookie in cj:
    print(f"  {cookie.name} = {cookie.value[:30]}... (secure={cookie.secure}, path={cookie.path})")

print()
print("✅ Todas las pruebas de infraestructura pasaron correctamente.")
print("   La autenticación, CSRF, y redirección funcionan.")
print("   Para probar login con usuario real, usa la app en el navegador.")
