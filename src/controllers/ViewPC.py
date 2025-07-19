import requests

url = "http://localhost:8080/mpu"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()  # Aquí tienes todo el objeto JSON como dict de Python
    # Puedes guardar ese dict en una variable, archivo, o clase
    print(data)  # Muestra todo el objeto completo
else:
    print(f"Error en la solicitud: {response.status_code}")
