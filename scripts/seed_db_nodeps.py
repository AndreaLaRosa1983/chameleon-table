#Seed script: creates test users in the database.
#Run this after starting the application with docker compose up -d.

#Usage:
# python scripts/seed_db.py

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost/api"

PLAYERS = [
    {"username": "player1", "email": "player1@test.com", "password": "password123"},
    {"username": "player2", "email": "player2@test.com", "password": "password123"},
    {"username": "player3", "email": "player3@test.com", "password": "password123"},
    {"username": "player4", "email": "player4@test.com", "password": "password123"},
    {"username": "player5", "email": "player5@test.com", "password": "password123"},
]


def register(player):
    """
    POST a single registration request using only the standard library
    (urllib.request), so the script has no external dependencies and works
    with any base Python 3 install.

    Returns (status_code, body_text).
    """
    data = json.dumps(player).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/register",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, res.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        # Non-2xx responses (e.g. 400 "already exists") raise HTTPError,
        # with the real status code and body still available on it.
        return e.code, e.read().decode("utf-8")


def seed():
    print(f"Connecting to {BASE_URL}...")
    errors = 0
    for p in PLAYERS:
        try:
            status, text = register(p)
            if status == 200:
                print(f"  [OK] {p['username']} created")
            elif status == 400:
                print(f"  [SKIP] {p['username']} already exists")
            else:
                print(f"  [ERROR] {p['username']}: {status} {text}")
                errors += 1
        except urllib.error.URLError:
            print(f"  [ERROR] Cannot conect to {BASE_URL}. Is the application running?")
            sys.exit(1)

    print()
    if errors == 0:
        print("Seed complete.All players are ready.")
        print()
        print("Credentials:")
        for p in PLAYERS:
            print(f"  username: {p['username']}  password: {p['password']}")
    else:
        print(f"Seed completed with {errors} error(s).")


if __name__ == "__main__":
    seed()