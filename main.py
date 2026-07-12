import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from agent.config import settings
from api.routes import router as api_router

app = FastAPI(title="AIQuantification", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": "AIQuantification",
        "version": "0.1.0",
        "description": "AI-powered quantitative trading agent",
        "config": {
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model or "default",
            "config_file": settings.loaded_path,
        },
        "endpoints": {
            "agent": {
                "chat": "POST /agent/chat - AI agent chat",
                "stream": "POST /agent/chat/stream - Streaming chat",
                "tools": "GET /agent/tools - List available tools",
            },
            "market": {
                "overview": "GET /market/{market}/overview",
                "quote": "POST /market/quote",
                "klines": "POST /market/klines",
            },
            "strategies": "GET /strategies",
            "backtest": "POST /backtest",
            "docs": "/docs",
        },
    }


@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AIQuantification Agent</title>
        <meta charset="utf-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, sans-serif; background: #0d1117; color: #c9d1d9; height: 100vh; display: flex; flex-direction: column; }
            .header { padding: 16px 24px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { font-size: 18px; color: #58a6ff; }
            .header .config-badge { font-size: 11px; color: #8b949e; background: #21262d; padding: 4px 10px; border-radius: 12px; border: 1px solid #30363d; }
            .chat { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }
            .msg { max-width: 80%; padding: 12px 16px; border-radius: 8px; line-height: 1.5; white-space: pre-wrap; }
            .user { background: #1f6feb; align-self: flex-end; }
            .assistant { background: #21262d; align-self: flex-start; border: 1px solid #30363d; }
            .input-area { padding: 16px 24px; background: #161b22; border-top: 1px solid #30363d; display: flex; gap: 12px; }
            input { flex: 1; padding: 10px 16px; border-radius: 6px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; font-size: 14px; }
            button { padding: 10px 24px; border-radius: 6px; border: none; background: #238636; color: #fff; font-size: 14px; cursor: pointer; }
            button:hover { background: #2ea043; }
            button:disabled { opacity: 0.5; cursor: not-allowed; }
            .loading { color: #8b949e; font-style: italic; }
            .error { border-color: #da3633 !important; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>AIQuantification <span style="color:#8b949e;font-size:12px;margin-left:8px;">Quant Trading Agent</span></h1>
            <span class="config-badge">config.yaml</span>
        </div>
        <div class="chat" id="chat"></div>
        <div class="input-area">
            <input id="input" placeholder="分析 AAPL 的近期走势..." onkeydown="if(event.key==='Enter') send()"/>
            <button id="sendBtn" onclick="send()">发送</button>
        </div>
        <script>
            let sessionId = crypto.randomUUID();
            const chat = document.getElementById('chat');

            async function send() {
                const input = document.getElementById('input');
                const btn = document.getElementById('sendBtn');
                const query = input.value.trim();
                if (!query) return;

                input.value = '';
                btn.disabled = true;

                addMsg(query, 'user');

                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'msg assistant loading';
                loadingDiv.textContent = '分析中...';
                chat.appendChild(loadingDiv);
                chat.scrollTop = chat.scrollHeight;

                try {
                    const resp = await fetch('/agent/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({query, session_id: sessionId})
                    });
                    const data = await resp.json();
                    loadingDiv.remove();
                    addMsg(data.answer, 'assistant');
                    sessionId = data.session_id;
                } catch(e) {
                    loadingDiv.remove();
                    addMsg('Error: ' + e.message, 'assistant');
                } finally {
                    btn.disabled = false;
                    input.focus();
                }
            }

            function addMsg(text, role) {
                const div = document.createElement('div');
                div.className = 'msg ' + role;
                div.textContent = text;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }
        </script>
    </body>
    </html>
    """)
