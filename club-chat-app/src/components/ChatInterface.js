import { useState, useRef, useEffect, useLayoutEffect } from 'react';
import axios from 'axios';
import { PaperAirplaneIcon, ClipboardIcon, PaperClipIcon } from '@heroicons/react/solid';
import { v4 as uuidv4 } from 'uuid';

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [attachedFile, setAttachedFile] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const CHUNK_SIZE = 1 * 1024 * 1024; // 1 MB chunks

  // Generate a unique session ID for each user
  useEffect(() => {
    const storedSessionId = localStorage.getItem('sessionId') || uuidv4();
    localStorage.setItem('sessionId', storedSessionId);
    setSessionId(storedSessionId);
  }, []);

  // Preload the chatbot icon
  useEffect(() => {
    const preloadChatbotIcon = new Image();
    preloadChatbotIcon.src = '/chatbot_icon.png';
  }, []);

  // Scroll to the bottom of the chat window when new messages are added
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Scroll to the bottom when new messages are added
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Adjust the textarea height based on the content
  const adjustTextareaHeight = () => {
    const textarea = inputRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  };

  // Adjust the textarea height when the input changes
  useLayoutEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  // Handle input changes
  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  // Handle file uploads
  const handleFileChange = (e) => {
    const file = e.target.files[0];
      // Check for allowed file types (PDFs and images)
      const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif'];
      if (!allowedTypes.includes(file.type)) {
        alert('Please select a valid PDF or image file.');
        return;
      }
    setAttachedFile(file);
  };

  // Send a message
  const sendMessage = async () => {
    if (!input.trim() && !attachedFile) return;
  
    // Create a unique ID for the user message
    const uniqueId = Date.now();
    const userMessage = createUserMessage(uniqueId);
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput('');
    const fileToSend = attachedFile; // Preserve the file for async operations
    setAttachedFile(null);
  
    try {
      setIsTyping(true);
  
      if (fileToSend) {
        await handleFileUpload(fileToSend, uniqueId);
      } else {
        await handleTextMessage(input, uniqueId);
      }
    } catch (error) {
      handleError(uniqueId);
    } finally {
      setIsTyping(false);
    }
  };
  
  const createUserMessage = (uniqueId) => ({
    sender: 'user',
    text: formatMessageText(),
    timestamp: new Date(),
    id: uniqueId,
  });
  
  const formatMessageText = () => {
    if (input && attachedFile) return `${input}\n\n(Attached file: ${attachedFile.name})`;
    if (input) return input;
    if (attachedFile) return `Attached file: ${attachedFile.name}`;
    return '';
  };
  
  const handleFileUpload = async (file, uniqueId) => {
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    const fileId = uuidv4();
    let botResponse = '';
  
    for (let i = 0; i < totalChunks; i++) {
      const chunk = file.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE);
      const formData = createFileUploadFormData(chunk, file, i, totalChunks, fileId);
  
      if (i === totalChunks - 1) {
        formData.append('message', input || '');
      }
  
      const response = await axios.post('/api/chat', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
  
      if (i === totalChunks - 1) {
        botResponse = response.data.response;
      }
    }
  
    if (botResponse) {
      addBotMessage(botResponse, uniqueId + 1);
    }
  };
  
  const createFileUploadFormData = (chunk, file, chunkIndex, totalChunks, fileId) => {
    const formData = new FormData();
    formData.append('chunk', chunk);
    formData.append('chunkIndex', chunkIndex);
    formData.append('totalChunks', totalChunks);
    formData.append('fileId', fileId);
    formData.append('fileName', file.name);
    formData.append('fileType', file.type);
    formData.append('sessionId', sessionId);
    return formData;
  };
  
  const handleTextMessage = async (text, uniqueId) => {
    const response = await axios.post('/api/chat', {
      message: text,
      sessionId,
    });
  
    const botResponseText =
      typeof response.data === 'object'
        ? response.data.response || JSON.stringify(response.data)
        : response.data || 'No response';
  
    addBotMessage(botResponseText, uniqueId + 1);
  };
  
  const addBotMessage = (text, id) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      {
        sender: 'bot',
        text,
        timestamp: new Date(),
        id,
      },
    ]);
  };
  
  const handleError = (uniqueId) => {
    console.error('Error occurred while sending the message.');
    addBotMessage('An error occurred. Please try again.', uniqueId + 2);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(
      () => console.log('Text copied to clipboard'),
      (err) => console.error('Could not copy text:', err)
    );
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="bg-primary-light text-white p-4 flex items-center">
        <img
          src="/ieeeutdlogo.png"
          alt="IEEE UTD Logo"
          className="w-10 h-10 mr-4"
        />
        <h1 className="text-xl font-bold">IEEE Chatbot</h1>
      </header>
      <div className="flex flex-col flex-grow overflow-hidden">
        <div className="flex-grow p-4 overflow-y-auto">
          <div className="max-w-2xl mx-auto">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex mb-4 ${
                  msg.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.sender === 'bot' && (
                  <div className="flex-shrink-0 mr-2">
                    <img
                      src="/chatbot_icon.png"
                      alt="Bot Avatar"
                      className="w-8 h-8 rounded-full"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = '/default_user.png';
                      }}
                    />
                  </div>
                )}
                <div className="relative">
                  <div
                    className={`p-3 rounded-lg max-w-xs ${
                      msg.sender === 'user'
                        ? 'bg-primary-light text-white'
                        : 'bg-white text-gray-800'
                    }`}
                    style={{ whiteSpace: 'pre-wrap' }}
                  >
                    {msg.text}
                  </div>
                  <button
                    className="absolute top-0 right-0 mt-1 mr-1 text-gray-500 hover:text-gray-700"
                    onClick={() => copyToClipboard(msg.text)}
                    aria-label="Copy message"
                  >
                    <ClipboardIcon className="h-4 w-4" />
                  </button>
                  <div className="text-xs text-gray-500 mt-1">
                    {msg.timestamp.toLocaleTimeString()}
                  </div>
                </div>
                {msg.sender === 'user' && (
                  <div className="flex-shrink-0 ml-2">
                    <img
                      src="/default_user.png"
                      alt="User Avatar"
                      className="w-8 h-8 rounded-full"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = '/default_user.png';
                      }}
                    />
                  </div>
                )}
              </div>
            ))}
            {isTyping && (
              <div className="flex mb-4 justify-start">
                <div className="flex-shrink-0 mr-2">
                  <img
                    src="/chatbot_icon.png"
                    alt="Bot Avatar"
                    className="w-8 h-8 rounded-full"
                  />
                </div>
                <div>
                  <div className="p-3 rounded-lg max-w-xs bg-white text-gray-800">
                    Bot is typing...
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
        <div className="bg-white p-4 flex justify-center items-center flex-shrink-0">
          <div className="max-w-2xl w-full flex items-end">
            <label
              htmlFor="file-upload"
              className="flex items-center justify-center bg-gray-200 text-gray-600 px-4 py-2 rounded-l-md cursor-pointer"
              style={{
                height: '40px',
                minHeight: '40px',
              }}
            >
              <PaperClipIcon className="h-5 w-5" />
              <input
                id="file-upload"
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                className="hidden"
                onChange={handleFileChange}
              />
            </label>
            <textarea
              ref={inputRef}
              placeholder="Type your message..."
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              className="flex-grow border border-gray-300 p-2 focus:outline-none text-black placeholder-gray-500 resize-none overflow-y-auto"
              style={{ maxHeight: '120px' }}
              rows={1}
            />
            <button
              onClick={sendMessage}
              className="bg-primary-light text-white px-4 py-2 rounded-r-md hover:bg-primary-dark flex items-center"
              style={{
                height: '40px',
              }}
            >
              <PaperAirplaneIcon className="h-5 w-5 mr-1 transform rotate-90" />
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
