"""
Primer modula za demonstraciju AI Test Generator-a i AI Security Analyzer-a.
Sadrzi tipicne funkcije koje bi se nasle u realnom projektu, ukljucujuci
i namerno unetu bezbednosnu manu (SQL injection) radi demonstracije
AI Security Analyzer-a.
"""

import hashlib
import re
import sqlite3


def validate_and_hash_password(password: str) -> str:
    """Validira jacinu lozinke i vraca njen hash.
    Raises ValueError ako lozinka ne zadovoljava kriterijume.
    """
    if len(password) < 8:
        raise ValueError("Lozinka mora imati minimum 8 karaktera")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Lozinka mora sadrzati veliko slovo")
    if not re.search(r"[0-9]", password):
        raise ValueError("Lozinka mora sadrzati cifru")

    return hashlib.sha256(password.encode()).hexdigest()


def get_user_by_username(db_path: str, username: str):
    """NAMERNO RANJIVA funkcija - SQL injection radi demonstracije
    AI Security Analyzer-a. NE koristiti ovakav pattern u produkciji!
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"  # ranjivo!
    cursor.execute(query)
    return cursor.fetchone()


def calculate_discount(price: float, discount_percent: float) -> float:
    """Racuna cenu nakon popusta."""
    if not 0 <= discount_percent <= 100:
        raise ValueError("Procenat popusta mora biti izmedju 0 i 100")
    if price < 0:
        raise ValueError("Cena ne moze biti negativna")
    return round(price * (1 - discount_percent / 100), 2)
