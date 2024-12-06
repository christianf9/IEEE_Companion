import os
import tiktoken
import threading

encoding = tiktoken.encoding_for_model("gpt-4o-mini-2024-07-18")

lock = threading.Lock()

UPLOAD_FOLDER = './uploads'

def count_tokens(messages):
    num_tokens = 0
    for message in messages:
        num_tokens += 4
        num_tokens += len(encoding.encode(message['content']))
    num_tokens += 2
    return num_tokens

def chunk_text(text, max_length=400):
    """
    Splits text into smaller chunks for embedding.
    """
    sentences = text.split(". ")
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def reassemble_file(file_id, total_chunks, file_type, session_id):
    with lock:
        chunk_paths = [
            os.path.join(UPLOAD_FOLDER, f"{file_id}.{i}") for i in range(total_chunks)
        ]

        extension = file_type.split('/')[1]

        if extension != 'pdf':
            reassembled_file_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_image.{extension}")
        else:
            reassembled_file_path = os.path.join(UPLOAD_FOLDER, f"{session_id}.{extension}")
        

        with open(reassembled_file_path, 'wb') as out_file:
            for chunk_path in chunk_paths:
                with open(chunk_path, 'rb') as chunk_file:
                    out_file.write(chunk_file.read())
                os.remove(chunk_path)  # Clean up the chunk file

        return reassembled_file_path