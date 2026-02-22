# AI Tour Concierge

This project is a static, React-based AI Tour Concierge chat interface for Microsoft AI Tour events. It helps attendees with session information, FAQs, and more. (Working in progress)

## Folder Structure

```
ai-tour-london/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   └── MessageBubble.jsx
│   │   ├── ag-ui/
│   │   │   └── agentClient.js
│   │   ├── pages/
│   │   │   └── App.jsx
│   │   └── index.js
│   ├── public/
│   │   └── index.html
│   └── package.json
├── data/           # Event/session data (optional, if used by frontend)
├── infra/          # Azure Bicep templates (optional)
├── azure.yaml      # Azure deployment config
├── .env            # Environment variables (optional)
└── README.md
```


## Architecture 


This project consists of a static React frontend and a Python FastAPI backend, both containerized and deployed to Azure Container Apps.

- **Frontend:** React SPA (Single Page Application) served by Nginx.
- **Backend:** Python FastAPI app, containerized and deployed to Azure Container Apps. The backend exposes a `/chat` endpoint that routes requests to local agents (FAQ, session, personalized) via an orchestrator. All agent logic is handled locally; there is no MCP server integration for this demo.
- **Foundry Integration:**
   - **Session agent** is grounded in `data/schedule-data-all.json` using the file search tool in Foundry. All session-related responses are based on the latest content in this JSON file.
   - **FAQ agent** is grounded in `data/faq.md` using the file search tool in Foundry. All FAQ responses are based on the latest content in this Markdown file.
- **Data:** Static assets and optional JSON data files in the `data/` directory.



## How to Run Locally

1. Navigate to `frontend/`
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the frontend in development mode:
   ```bash
   npm start
   ```
4. For production/static hosting, build and serve with Nginx or any static server:
   ```bash
   npm run build
   # Serve the build/ directory with your preferred static server or Dockerfile
   ```


## Deployment

This project is ready for deployment as a static site using Nginx and Azure Container Apps.

1. Build the Docker image (for Azure, use amd64 platform):
   ```bash
   docker buildx build --platform linux/amd64 -t <your-registry>/ai-tour-frontend:latest ./frontend --push
   ```
   Replace `<your-registry>` with your Azure Container Registry name.
2. Deploy to Azure Container Apps using `azure.yaml` or the Azure Portal.


## Environment Variables

If your frontend needs to call APIs, set the appropriate API endpoint URLs in `.env` or your deployment environment.


## API Endpoints

- `POST /chat` — Accepts `{ "agent": "session|faq|personalized", "message": "..." }` and returns `{ "response": "..." }`.

## Project Structure

This project includes both frontend and backend code. The backend is minimal and does not use MCP server integration for this demo.
