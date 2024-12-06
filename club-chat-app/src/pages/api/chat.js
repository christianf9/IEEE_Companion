// src/pages/api/chat.js

import fs from 'fs';
import formidable from 'formidable';
import axios from 'axios';
import FormData from 'form-data';

export const config = {
  api: {
    bodyParser: false, // Disable Next.js bodyParser for raw data with formidable
  },
};

const parseForm = (req) =>
  new Promise((resolve, reject) => {
    const form = formidable({ maxFileSize: 10 * 1024 * 1024 }); // 10MB limit per chunk
    form.parse(req, (err, fields, files) => {
      if (err) return reject(err);
      resolve({ fields, files });
    });
  });

export default async function handler(req, res) {
  if (req.method === 'POST') {
    try {
      if (req.headers['content-type']?.includes('multipart/form-data')) {
        const { fields, files } = await parseForm(req);

        const chunkIndex = fields.chunkIndex[0];
        const totalChunks = parseInt(fields.totalChunks[0], 10);
        const fileId = fields.fileId[0];
        const sessionId = fields.sessionId[0];
        const fileName = fields.fileName[0];
        const fileType = fields.fileType[0];
        const message = fields.message ? fields.message[0] : ''; // Default to empty if no message is provided
        const chunk = files.chunk[0];

        console.log("file_type: ", fileType);

        console.log("message: ", message);

        // Validate required fields
        if (!chunkIndex || !totalChunks || !fileId || !sessionId) {
          return res.status(400).json({ error: 'Invalid data' });
        }

        // Read the chunk file and convert it to a Blob-compatible stream
        const chunkBuffer = fs.readFileSync(chunk.filepath);
        const flaskUrl = process.env.CHATBOT_API;

        const formData = new FormData();
        formData.append('file_chunk', chunkBuffer, {
          filename: `chunk_${chunkIndex}`,
          contentType: 'application/octet-stream',
        });
        formData.append('file_id', fileId);
        formData.append('chunk_index', chunkIndex);
        formData.append('total_chunks', totalChunks);
        formData.append('session_id', sessionId);
        formData.append('file_type', fileType);

        // Send the chunk to the Flask API
        await axios.post(flaskUrl, formData, {
          headers: {
            ...formData.getHeaders(),
          },
        });

        console.log(`Chunk ${chunkIndex} uploaded`);
        console.log(`Total chunks: ${totalChunks}`);

        // Check if it's the final chunk
        if (chunkIndex == totalChunks - 1) {
          console.log('Final chunk uploaded');
          console.log("message: ", message);
          // After the final chunk, send the message
          const payload = {
            session_id: sessionId,
            input_text: message,
            file_id: fileId,
            file_type: fileType,
          };

          try {
            const response = await axios.post(flaskUrl, payload, {
              headers: {
                'Content-Type': 'application/json',
              },
            });

            res.status(200).json({
              message: 'File fully uploaded and processed',
              response: response.data.response,
            });
          } catch (error) {
            console.error('Error sending message to Flask API:', error.response?.data || error.message);
            res.status(500).json({ error: 'Failed to send the message to the chatbot API' });
          }
        } else {
          res.status(200).json({ message: `Chunk ${chunkIndex} uploaded` });
        }
      } else {
        // Handle cases where only session ID and optional message are sent
        let body = '';
        req.on('data', (chunk) => {
          body += chunk;
        });

        req.on('end', async () => {
          const { message, sessionId } = JSON.parse(body);
          if (!sessionId) {
            return res.status(400).json({ error: 'Session ID is required' });
          }

          const payload = { session_id: sessionId, input_text: message || '' };
          const flaskUrl = process.env.CHATBOT_API;

          try {
            const response = await axios.post(flaskUrl, payload, {
              headers: {
                'Content-Type': 'application/json',
              },
            });

            res.status(200).json({ response: response.data.response });
          } catch (error) {
            console.error('Error sending message to Flask API:', error.response?.data || error.message);
            res.status(500).json({ error: 'Failed to send the message to the chatbot API' });
          }
        });
      }
    } catch (error) {
      console.error('Error handling user request:', error);
      res.status(500).json({ error: 'An error occurred' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
