import React from 'react';

const MessageBubble = ({ sender, text }) => (
  <div style={{
    textAlign: sender === 'user' ? 'right' : 'left',
    margin: '8px 0',
    color: sender === 'user' ? '#1976d2' : '#333',
    background: sender === 'user' ? '#e3f2fd' : '#f1f1f1',
    borderRadius: 8,
    padding: 8,
    display: 'inline-block',
    maxWidth: '80%'
  }}>
    <b>{sender === 'user' ? 'You' : sender === 'agent' ? 'Concierge' : 'System'}:</b> {text}
  </div>
);

export default MessageBubble;
