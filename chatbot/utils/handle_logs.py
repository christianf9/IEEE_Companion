import os

def get_next_dialogue_file():
    os.makedirs("./results", exist_ok=True)
    
    index = 1
    while True:
        filename = f"./results/test_dialogue_{index}.txt"
        if not os.path.exists(filename):
            return filename
        index += 1

def log_chat_entry(filename, role, message):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"{role}: {message}\n")