#Seed script: creates test users in the database.
#Run this after starting the application with docker compose up -d.

import httpx
import sys

BASE_URL = "http://localhost/api"

PLAYERS = [
    {"username": "player1", "email": "player1@test.com", "password": "password123"},
    {"username": "player2", "email": "player2@test.com", "password": "password123"},
    {"username": "player3", "email": "player3@test.com", "password": "password123"},
    {"username": "player4", "email": "player4@test.com", "password": "password123"},
    {"username": "player5", "email": "player5@test.com", "password": "password123"},
]

def seed():
    print(f"Connecting to {BASE_URL}...")
    errors = 0
    for p in PLAYERS:
        try:
            res = httpx.post(f"{BASE_URL}/register", json=p, timeout=10)
            if res.status_code == 200:
                print(f"  [OK] {p['username']} created")
            elif res.status_code == 400:
                print(f"  [SKIP] {p['username']} already exists")
            else:
                print(f"  [ERROR] {p['username']}: {res.status_code} {res.text}")
                errors += 1
        except httpx.ConnectError:
            print(f"  [ERROR] Cannot conect to {BASE_URL}. Is the application running?")
            sys.exit(1)

    print()
    if errors == 0:
        print("Seed complete. All players are ready.")
        print()
        print("Credentials:")
        for p in PLAYERS:
            print(f"  username: {p['username']}  password: {p['password']}")
    else:
        print(f"Seed completed with {errors} error(s).")

if __name__ == "__main__":
    seed()