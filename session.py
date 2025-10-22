import json
import os
from PyQt5.QtGui import QPixmap

SESSION_FILE = "session.json"
IMG_DIR = "img"

def gather_session():
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR, exist_ok=True)

    try:
        from BrowserWindow import BrowserWindow
        instances = getattr(BrowserWindow, "instances", []) or []
    except Exception:
        instances = []

    data = []
    for w in instances:
        win_tabs = []
        for i in range(w.tabs.count()):
            tab = w.tabs.widget(i)
            view = getattr(tab, "view", None)
            url = view.url().toString()
            if url != "about:blank":
                win_tabs.append(url)
        data.append(win_tabs)
    return data

def save_full_session():
    data = gather_session()
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Session saved to", SESSION_FILE)
    except Exception as e:
        print("Error saving session:", e)

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print("Error loading session:", e)
        return None