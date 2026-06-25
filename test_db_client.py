import re
with open("backend/services/db_client.py", "r") as f:
    text = f.read()

def count_duplicates(text):
    print("Length of file:", len(text))

count_duplicates(text)
