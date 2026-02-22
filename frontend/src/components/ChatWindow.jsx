
import React, { useState } from 'react';
import MessageBubble from './MessageBubble';
import agentClient from '../ag-ui/agentClient';

const AGENTS = [
  { key: 'session', label: '📅 Sessions' },
  { key: 'faq', label: '❓ FAQ' },
  { key: 'personalized', label: '✨ Personalized' }
];


const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [currentAgent, setCurrentAgent] = useState('session');

  const sendMessage = async () => {
    if (!input.trim()) return;
    setMessages([...messages, { sender: 'user', text: input, agent: currentAgent }]);
    const res = await agentClient(input, currentAgent);
    setMessages(msgs => [...msgs, { sender: 'agent', text: res, agent: currentAgent }]);
    setInput('');
  };

  return (
    <div className="app">
      <header>
        <div className="logo">🎯</div>
        <div>
          <h1>AI Tour Concierge</h1>
          <p>Microsoft AI Tour London • Feb 24, 2026</p>
        </div>
      </header>
      <div className="agents">
        {AGENTS.map(agent => (
          <button
            key={agent.key}
            className={`agent-btn${currentAgent === agent.key ? ' active' : ''}`}
            onClick={() => setCurrentAgent(agent.key)}
          >
            {agent.label}
          </button>
        ))}
      </div>
      <div className="chat-container">
        {messages.length === 0 && (
          <div className="welcome">
            <h2>Welcome to AI Tour London!</h2>
            <p>Ask me about sessions, venue info, or learning resources.</p>
            <div className="suggestions">
              <div className="suggestion" onClick={() => setInput("What sessions are happening today?")}>📅 Today's sessions</div>
              <div className="suggestion" onClick={() => setInput("Where is the event located?")}>📍 Venue info</div>
              <div className="suggestion" onClick={() => setInput("Find sessions about AI agents")}>🤖 AI agents talks</div>
              <div className="suggestion" onClick={() => setInput("Learn resources for Azure AI")}>📚 Azure AI learning</div>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} sender={msg.sender} text={msg.text} agent={msg.agent} />
        ))}
      </div>
      <div className="input-area">
        <div className="input-wrapper">
          <input
            type="text"
            id="messageInput"
            placeholder="Ask about sessions, venue, or resources..."
            autoComplete="off"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={e => { if (e.key === 'Enter') sendMessage(); }}
          />
          <button id="sendBtn" onClick={sendMessage}>Send</button>
        </div>
      </div>
      <div className="footer">Powered by <a href="https://ai.azure.com">Azure AI Foundry</a></div>
    </div>
  );
};

export default ChatWindow;
