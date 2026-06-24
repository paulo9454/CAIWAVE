import os

def is_demo():
    return os.getenv("APP_MODE", "production") == "demo"
