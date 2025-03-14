#!/bin/bash

# Kill any processes using port 8000 and 3000
echo "Checking for processes using ports 8000 and 3000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start the MCP server in the background
echo "Starting MCP server..."
python run.py &
MCP_PID=$!

# Wait a moment for the MCP server to initialize
sleep 3

# Start the ChatGPT AI template
echo "Starting ChatGPT AI template..."
cd chatgpt-ai-template
npm run dev

# When the npm process exits, kill the MCP server
kill $MCP_PID 2>/dev/null || true 