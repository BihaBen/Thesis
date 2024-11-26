import requests

def update_milestone(id: int, completed: bool):
    url = "http://localhost:8000/update_milestone"
    payload = {"id": id, "completed": completed}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"Mérföldkő frissítve: ID {id}, Állapot: {completed}")
        else:
            print(f"Hiba történt: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Nem sikerült elérni az API-t: {e}")