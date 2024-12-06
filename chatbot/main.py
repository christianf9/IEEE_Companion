from flask import Flask, request, jsonify
import os
import threading
import tiktoken
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import openai
from dotenv import load_dotenv
from rag_core import KnowledgeFlow
from tools_schema import TOOLS
from tools_functions import handle_tool_call
import json
import re
from utils.handle_pdfs import *
from utils.handle_logs import *
from prompts import SYSTEM_PROMPT, ADMIN_SYSTEM_PROMPT

# Add this variable at the start of your app initialization
dialogue_file = None

admin_ids = set()

# Load environment variables
load_dotenv()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize MongoDB client
mongo_db_client = MongoClient(os.getenv("MONGODB_URI"))
db = mongo_db_client["chatBot"]
tutors_collection = db["tutors"]
events_collection = db["events"]
rules_collection = db["rules"]

# Initialize sentence transformer model for embeddings
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Initialize KnowledgeFlow
dimension = 384  # SentenceTransformer embedding size
vector_db_name = "chatBot"
index_collection_name = "vector_indices"
texts_collection_name = "vector_texts"
knowledge_flow = None  # Will initialize after defining the KnowledgeFlow class

# Initialize KnowledgeFlow after defining the class
knowledge_flow = KnowledgeFlow(
    mongo_db_client,
    vector_db_name,
    index_collection_name,
    texts_collection_name,
    dimension
)


# Initialize Flask app
app = Flask(__name__)

# Directory for temporary file storage
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Dictionaries to track the state
session_histories = {}
file_states = {}
lock = threading.Lock()

# Initialize the tokenizer
encoding = tiktoken.encoding_for_model("gpt-4o-mini-2024-07-18")

def process_pdf(file_path, session_id):
    print(f"Processing PDF: {file_path}")
    text = extract_text(file_path)
    if not text:
        return None
    
    text = text.replace('\n', ' ').replace('  ', ' ')  # Remove newlines and double spaces

    text_chunks = chunk_text(text)

    # Generate embeddings and store in the vector database
    vectors = model.encode(text_chunks, convert_to_numpy=True)
    knowledge_flow.create_or_update_vector_store(session_id, vectors, text_chunks)

    return text_chunks

def respond(user_message, session_id):
    global session_histories
    with lock:
        # Initialize session history if it doesn't exist for the session ID
        if session_id not in session_histories:
            session_histories[session_id] = []

        # Append user's message to the session-specific conversation history
        session_histories[session_id].append({"role": "user", "content": user_message})

        # Generate embedding for the user's message
        user_embedding = model.encode([user_message], convert_to_numpy=True)

        # Use KnowledgeFlow to retrieve relevant texts
        try:
            relevant_texts = knowledge_flow.search_vector_store(session_id, user_embedding[0], k=5)
        except Exception as e:
            print(f"Error retrieving relevant texts: {e}")
            relevant_texts = []


        # Prepare the knowledge context
        knowledge_context = "\n".join(relevant_texts)
        knowledge_tokens = len(encoding.encode(knowledge_context))
        max_knowledge_tokens = 2000  # Limit for the KnowledgeFlow context
        if knowledge_tokens > max_knowledge_tokens:
            # Truncate the context to fit within the token limit
            knowledge_context = encoding.decode(encoding.encode(knowledge_context)[:max_knowledge_tokens])

        # Prepare the chat history context
        chat_history = session_histories[session_id]
        max_history_tokens = 1000  # Limit for the chat history
        history_tokens = count_tokens(chat_history)

        # Trim the chat history if it exceeds the limit
        while history_tokens > max_history_tokens:
            if len(chat_history) > 1:
                chat_history = chat_history[2:]  # Remove the oldest exchanges
                history_tokens = count_tokens(chat_history)
            else:
                break

        # Define a clear delimiter for the model
        delimiter = "\n\n--- CONTEXT BREAK ---\n\n"

        # Format the chat history using a list comprehension
        chat_history_formatted = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])

        # Combine the contexts with the delimiter
        full_context = (
            f"Relevant knowledge context:\n{knowledge_context}"
            f"{delimiter}"
            f"Chat history:\n{chat_history_formatted}"
        )

        # Prepare the messages to send to the OpenAI API, if user is an admin use ADMIN_SYSTEM_PROMPT, else use SYSTEM_PROMPT
        if session_id in admin_ids:
            messages = [
                {"role": "system", "content": ADMIN_SYSTEM_PROMPT},
                {"role": "system", "content": f"Here is the combined context:\n{full_context}"}
            ]
        else:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": f"Here is the combined context:\n{full_context}"}
            ]

        # Define token limits
        MAX_TOKENS = 4096
        MAX_RESPONSE_TOKENS = 500
        MAX_ALLOWED_TOKENS = MAX_TOKENS - MAX_RESPONSE_TOKENS

        # Trim conversation history further if necessary to fit within token limits
        while count_tokens(messages) > MAX_ALLOWED_TOKENS:
            if len(chat_history) > 1:
                chat_history = chat_history[2:]  # Remove the oldest exchanges
                history_tokens = count_tokens(chat_history)
                # Update the full context
                chat_history_formatted = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
                full_context = (
                    f"Relevant knowledge context:\n{knowledge_context}"
                    f"{delimiter}"
                    f"Chat history:\n{chat_history_formatted}"
                )
                messages[1]["content"] = f"Here is the combined context:\n{full_context}"
            else:
                break

        try:
            os.makedirs("./messages", exist_ok=True)

            # Save the messages to a text file for debugging
            with open(f"./messages/{session_id}_messages{len(session_histories[session_id])}.txt", "w") as f:
                for message in messages:
                    f.write(f"{message['role']}: {message['content']}\n")

            # Call the OpenAI API to generate a response
            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            
            assistant_message = response.choices[0].message
            
            # Handle tool calls in the assistant's response
            if assistant_message.tool_calls:
                function_responses = []
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    function_response = handle_tool_call(
                        tutors_collection,
                        rules_collection,
                        events_collection,
                        function_name,
                        function_args,
                        session_id,
                        admin_ids
                    )
                    
                    function_responses.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    })

                    print(function_responses)
                
                # Include tool responses in the final response, if user is an admin use ADMIN_SYSTEM_PROMPT, else use SYSTEM_PROMPT
                if session_id in admin_ids:
                    messages = [
                        {"role": "system", "content": ADMIN_SYSTEM_PROMPT},
                        *session_histories[session_id],
                        assistant_message,
                        *function_responses
                    ]
                else:
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *session_histories[session_id],
                        assistant_message,
                        *function_responses
                    ]
                
                print(f"Messages with tool responses: {messages}")
                final_response = client.chat.completions.create(
                    model="gpt-4o-mini-2024-07-18",
                    messages=messages,
                )
                
                bot_response = final_response.choices[0].message.content.strip()
            else:
                bot_response = assistant_message.content.strip()
            
            session_histories[session_id].append({"role": "assistant", "content": bot_response})
            return bot_response

        except openai.OpenAIError as e:
            print(f"Error: {e}")
            return "Sorry, I encountered an error while processing your request."


@app.route("/chat", methods=["POST"])
def chat():
    if 'file_chunk' in request.files:
        # Handle file chunk uploads
        chunk = request.files['file_chunk']
        file_id = request.form.get('file_id')
        chunk_index = int(request.form.get('chunk_index', -1))
        total_chunks = int(request.form.get('total_chunks', -1))
        session_id = request.form.get('session_id')

        file_type = request.form.get('file_type')

        print(file_type)

        if not file_id or chunk_index < 0 or total_chunks <= 0 or not session_id:
            return jsonify({"error": "Invalid file upload data"}), 400

        # Save the chunk
        chunk_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.{chunk_index}")
        chunk.save(chunk_path)

        # Update file state
        with lock:
            if file_id not in file_states:
                file_states[file_id] = {"chunks_received": set(), "total_chunks": total_chunks}
            file_states[file_id]["chunks_received"].add(chunk_index)

        # Check if all chunks are received
        if len(file_states[file_id]["chunks_received"]) == total_chunks:
            # Reassemble the file
            reassembled_file_path = reassemble_file(file_id, total_chunks, file_type, session_id)
            file_states[file_id]["file_path"] = reassembled_file_path
            file_states[file_id]["file_type"] = file_type
            print(f"File {file_id} reassembled at {reassembled_file_path}.")

        return jsonify({"message": f"Chunk {chunk_index} received."})

    else:
        # Handle chat messages
        data = request.get_json()
        user_message = data.get("input_text", "")
        session_id = data.get("session_id")
        file_id = data.get("file_id")  # Optional

        # Log the original user message before any modification
        log_chat_entry(dialogue_file, "User", user_message)

        password_pattern = r"%\d{3}-\d{2}-\d{3}%"
        match_password = re.search(password_pattern, user_message)

        if match_password:
            if match_password.group(0) == ADMIN_PASSWORD:
                admin_ids.add(session_id)
                user_message = re.sub(password_pattern, "%VALID_PASSWORD%", user_message)
            else:
                user_message = re.sub(password_pattern, "%INVALID_PASSWORD%", user_message)

        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400

        # If file_id is provided, ensure the file is processed
        if file_id:
            # Ensure the file is fully reassembled and processed
            if file_id not in file_states or "file_path" not in file_states[file_id]:
                return jsonify({"error": "File is not yet fully uploaded or processed."}), 400

            # Process the PDF if not already processed
            if "processed" not in file_states[file_id] and file_states[file_id]["file_type"] == "application/pdf":
                file_path = file_states[file_id]["file_path"]
                try:
                    process_pdf(file_path, session_id)
                    file_states[file_id]["processed"] = True
                    os.remove(file_path)
                    print(f"PDF {file_id} processed and vectorized.")
                except Exception as e:
                    print(f"Error processing PDF: {e}")
                    return jsonify({"error": "Failed to process the PDF."}), 500

        # Respond to the user's message
        bot_response = respond(user_message, session_id)
        log_chat_entry(dialogue_file, "Assistant", bot_response)
        return jsonify({"response": bot_response})
    
if __name__ == "__main__":
    dialogue_file = get_next_dialogue_file()
    print(f"Logging chat history to: {dialogue_file}")
    app.run(host="0.0.0.0", port=5000)
