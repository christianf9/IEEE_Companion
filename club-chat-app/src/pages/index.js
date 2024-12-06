// src/pages/index.js

import Head from 'next/head';
import ChatInterface from '../components/ChatInterface';

export default function Home() {
  return (
    <>
      <Head>
        <title>Chatbot Interface</title>
      </Head>
      <ChatInterface />
    </>
  );
}
