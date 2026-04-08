import requests

data = {
    "full_name": "Mamta User",
    "email": "mamta.se23@bitsathy.ac.in",
    "department": "COMPUTER SCIENCE AND ENGINEERING",
    "password": "password123",
    "role": "student"
}

res = requests.post("http://localhost:5000/api/register", json=data)
print("STATUS:", res.status_code)
print("RESPONSE:", res.text)
