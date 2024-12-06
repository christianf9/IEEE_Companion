# IEEE Companion

## Overview

The **IEEE Companion** is a chatbot solution designed to streamline the management and operations of student-run clubs like IEEE branches. It centralizes information dissemination, simplifies administrative tasks, and provides tools for club administrators and members to efficiently interact with club resources.

### Key Features
1. **Centralized Information Management**:
   - Unified database for tutors, events, and club rules.
   - Simplifies data retrieval and updates.

2. **File Upload and Knowledge Integration**:
   - Users can upload files (PDFs/images).
   - Extracts and stores document content for knowledge retrieval.

3. **Administrative Tools**:
   - Admin-only functionalities protected by password authentication.
   - Allows posting to club's Instagram without sharing credentials.

4. **Responsive User Interface**:
   - Built with **Next.js** and hosted on **Vercel**.
   - Mobile and desktop-friendly.

5. **AI-Powered Interaction**:
   - Leverages OpenAI GPT models for natural language understanding.
   - Enhanced by a Retrieval-Augmented Generation (RAG) system for knowledge-based responses.

## Setup Instructions

### Backend Setup (Flask)

1. Navigate to the chatbot directory:
```bash
cd chatbot
```

2. Create and activate the conda environment:
```bash
conda env create -f environment.yml -n custom_name
conda activate custom_name
```

3. Set up environment variables in a `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
MONGODB_URI=your_mongodb_uri
ADMIN_PASSWORD=your_admin_password
INSTAGRAM_USER=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
```

5. Start the Flask server:
```bash
python main.py
```

6. Create a public URL using ngrok (required for local development):
```bash
ngrok http 5000
```
Save the ngrok URL - this is required for the frontend to communicate with the backend when running locally. The URL will look something like `https://your-unique-id.ngrok.io`.

### Frontend Setup (Next.js)

1. Navigate to the frontend directory:
```bash
cd club-chat-app
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file in the root directory:
```env
CHATBOT_API=your_flask_endpoint  # Use ngrok URL if testing locally
```

4. Start the development server:
```bash
npm run dev
```

### Deployment

#### Vercel Deployment

1. Push your code to a GitHub repository

2. Connect your repository to Vercel:
   - Create a new project on Vercel
   - Import your GitHub repository
   - Add environment variables:
     - Set `CHATBOT_API` to your Flask backend endpoint

3. Deploy:
   - Vercel will automatically build and deploy your application
   - Any subsequent pushes to main will trigger automatic deployments

## Project Structure

```
.
├── chatbot/                 # Flask backend
│   ├── results/
│   │   ├── all_pdf_stats.txt                   # Results to test_pdf.py
│   │   ├── cleaning_extraction.txt             # Results to test_pdfminer.py
│   │   ├── test_dialogue_after_update.txt      # Chat logs after system prompt update
│   │   └── test_dialogue_before_update.txt     # Chat logs prior to system prompt update
│   ├── tests/
│   │   ├── test_pdf.py      # Code for testing various PDF text extractors
│   │   └── test_pdfminer.py # Code for testing text extraction cleaning
│   ├── utils/
│   │   ├── handle_logs.py   # Functions for logging
│   │   └── handle_pdfs.py   # Functions for processing PDFs
│   ├── main.py              # Main Flask application
│   └── prompts.py           # System Prompts for Chatbot
│   └── rag_core.py          # Core of RAG System
│   └── requirements.txt     # Python dependencies
│   └── tools_functions.py   # OpenAI Tools for the Chatbot
│   └── tools_schemas.py     # OpenAI Tool Schemas for the Chatbot
│
├── club-chat-app/           # Next.js frontend
│   ├── src/
│   │   ├── components/
│   │   │   └── ChatInterface.js    # Chat interface component
│   │   └── pages/
│   │       └── api/
│   │           └── chat.js          # API route handler
│   └── package.json
```

## Environment Variables

### Backend (.env)
- `OPENAI_API_KEY`: Your OpenAI API key
- `MONGODB_URI`: MongoDB connection string
- `ADMIN_PASSWORD`: Password for administrative access
- `INSTAGRAM_USER`: Username for club's Instagram account
- `INSTAGRAM_PASSWORD`: Password for club's Instagram account

### Frontend (.env.local)
- `CHATBOT_API`: URL of your Flask backend (e.g., ngrok URL for local testing or deployed endpoint)