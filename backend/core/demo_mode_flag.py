import os

def is_demo():
    return os.getenv("DEMO_MODE", "true").lower() == "true"
