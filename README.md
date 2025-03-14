# Custom MCP (Mission Control Panel) with ChatGPT AI Template

This project integrates a Custom MCP (Mission Control Panel) with a ChatGPT AI Template to provide an intelligent agentic system that integrates with Gmail and GitHub.

## Features

- **Gmail Integration**: Reads and analyzes emails from your Gmail account
- **GitHub Integration**: Interacts with GitHub repositories to check for issues, alerts, and other information
- **Intelligent Decision Making**: Uses OpenAI models to decide which tools to use and how to process information
- **Autonomous Operation**: Can autonomously navigate between different services to fulfill complex requests
- **Modern UI**: Beautiful and responsive UI built with Next.js and Chakra UI

## Example Use Cases

- "Check if there are any GitHub warnings in my Gmail"
- "Find dependency alerts for my repositories"
- "Summarize recent GitHub notifications"

## Technical Stack

- **Backend**: FastAPI (Python)
- **AI**: OpenAI API
- **External APIs**: Gmail API, GitHub API
- **Frontend**: Next.js, React, Chakra UI

## Project Structure

```
Custom-MCP/
├── src/                  # MCP Server
│   ├── api/              # API endpoints
│   ├── services/         # Service integrations (Gmail, GitHub, OpenAI)
│   ├── models/           # Data models
│   ├── utils/            # Utility functions
│   ├── config/           # Configuration management
│   └── main.py           # Application entry point
├── chatgpt-ai-template/  # ChatGPT AI Template
│   ├── app/              # Next.js app directory
│   ├── src/              # Source code
│   ├── public/           # Static assets
│   └── package.json      # Dependencies
├── .env                  # Environment variables (not in repo)
├── .env.example          # Example environment variables
├── requirements.txt      # Python dependencies
├── start.sh              # Script to start both servers
└── README.md             # This file
```

## Setup Instructions

### 1. MCP Server Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in a `.env` file (see `.env.example`)

3. Run the MCP server:
   ```bash
   python run.py
   ```

4. The MCP server will be available at `http://localhost:8000`

### 2. ChatGPT AI Template Setup

1. Navigate to the ChatGPT AI Template directory:
   ```bash
   cd chatgpt-ai-template
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. The ChatGPT AI Template will be available at `http://localhost:3000`

### 3. Quick Start (Both Servers)

For convenience, you can use the provided script to start both servers at once:

```bash
./start.sh
```

This script will:
1. Start the MCP server in the background
2. Wait for it to initialize
3. Start the ChatGPT AI Template frontend
4. Automatically stop the MCP server when you exit the frontend

## Configuration

You'll need to set up API credentials for:
- Gmail API (OAuth2)
- GitHub API (Personal Access Token)
- OpenAI API

See the `.env.example` file for required environment variables.

## Usage

1. Start both the MCP server and the ChatGPT AI Template as described above.
2. Open your browser and navigate to `http://localhost:3000`.
3. Click on the "MCP Chat" option in the sidebar to access the MCP Chat interface.
4. Enter your query in the input field and press Enter or click the Send button.
5. The MCP server will process your query and return a response.

## License

MIT 