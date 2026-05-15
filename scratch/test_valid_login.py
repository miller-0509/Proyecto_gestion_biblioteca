import http.cookiejar
import urllib.request
import urllib.parse
import re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Load login page to get CSRF token
resp = opener.open('http://127.0.0.1:81/')
html = resp.read().decode()
csrf = re.search(r'name="csrf_token"\s+value="([^"]+)"', html).group(1)

# 2. Login as brayan@gmail.com
data = urllib.parse.urlencode({'csrf_token': csrf, 'correo': 'brayan@gmail.com', 'password': '12345678Ab'}).encode()
resp2 = opener.open(urllib.request.Request('http://127.0.0.1:81/', data=data, method='POST'))
print('Login result URL:', resp2.url)
print('Is dashboard:', 'dashboard' in resp2.url)

# 3. Access dashboard
resp3 = opener.open('http://127.0.0.1:81/dashboard')
print('Dashboard status:', resp3.status)
html3 = resp3.read().decode()
match = re.search(r'<span class="ms-2 d-none d-lg-inline">([^<]+)</span>', html3)
print('Logged in as:', match.group(1) if match else 'NOT FOUND')
