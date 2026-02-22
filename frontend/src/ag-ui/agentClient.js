// agentClient.js

const API_URL = process.env.NODE_ENV === 'production'
  ? 'https://backend-ai-tour.salmonpebble-51056e35.eastus.azurecontainerapps.io'
  : '';

const agentClient = async (message, selectedAgent) => {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent: selectedAgent, message })
  });
  const data = await res.json();
  // Handle both string and object responses
  if (typeof data.response === 'object' && data.response !== null) {
    // Try to extract a useful string from known keys
    if (data.response.result) return data.response.result;
    if (data.response.answer) return data.response.answer;
    return JSON.stringify(data.response);
  }
  return data.response;
};

export default agentClient;