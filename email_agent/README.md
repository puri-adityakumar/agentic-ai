# AI Email Assistant

A FastAPI backend with LangGraph multi-agent system for email management - researches topics and sends results via email.

## Setup & Run

1. **Copy environment file:**
   ```bash
   cp .env.sample .env
   ```

2. **Configure .env with your credentials:**
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `EMAIL_ADDRESS` - Your Gmail address
   - `EMAIL_PASSWORD` - Gmail app password
   - Other vars as needed

3. **Start services:**
   ```bash
   docker compose up --build
   ```

4. **Access the API:**
   - API: http://localhost:8080
   - Health check: http://localhost:8080/health

## Example Usage

```bash
curl -X POST -d '{"message": "Research why it is good to go outside and email me the results"}' \
  -H "Content-Type: application/json" \
  http://localhost:8080/api/chats/
```
