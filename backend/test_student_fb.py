import requests

s = requests.Session()
data = {
    "email": "mamta.se23@bitsathy.ac.in",
    "password": "password123"
}
res = s.post("http://localhost:5000/api/login", json=data)
print("LOGIN:", res.status_code)

res = s.get("http://localhost:5000/api/student/my-feedback")
print("FEEDBACK RESPONSE CODE:", res.status_code)
print("FEEDBACK DATA:", res.json())
