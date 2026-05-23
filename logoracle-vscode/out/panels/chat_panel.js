"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChatPanel = void 0;
// src/panels/chat_panel.ts
const vscode = __importStar(require("vscode"));
class ChatPanel {
    static createOrShow(extensionUri, client) {
        if (ChatPanel.currentPanel) {
            ChatPanel.currentPanel._panel.reveal();
            return;
        }
        const panel = vscode.window.createWebviewPanel("logoracle.chat", "LogOracle Chat", vscode.ViewColumn.Beside, { enableScripts: true, retainContextWhenHidden: true });
        ChatPanel.currentPanel = new ChatPanel(panel, client);
    }
    constructor(panel, client) {
        this.client = client;
        this._sessionId = `vscode_${Date.now()}`;
        this._panel = panel;
        this._panel.webview.html = this._getHtml();
        this._panel.onDidDispose(() => { ChatPanel.currentPanel = undefined; });
        this._panel.webview.onDidReceiveMessage(async (msg) => {
            if (msg.type === "send") {
                await this._streamChat(msg.text, msg.persona, msg.mode);
            }
        });
    }
    async _streamChat(text, persona = "default", mode = "tech") {
        const payload = {
            message: text, persona, mode,
            session_context: {
                findings: [], last_log_lines: "", code_diff: "", chat_history: [],
                developer_profile: { expertise_level: "intermediate", past_quiz_scores: [], badges: [] }
            }
        };
        try {
            const res = await this.client.chatSync(payload, this._sessionId);
            const data = await res.json();
            const reply = data.reply || data.response || data.message || JSON.stringify(data);
            this._panel.webview.postMessage({ type: "token", token: reply });
            this._panel.webview.postMessage({ type: "done", intent: "" });
        }
        catch (e) {
            this._panel.webview.postMessage({ type: "error", message: e.message });
        }
    }
    _getHtml() {
        return `<!DOCTYPE html><html><head>
        <meta charset="UTF-8">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: var(--vscode-font-family); background: var(--vscode-editor-background);
                   color: var(--vscode-foreground); display: flex; flex-direction: column; height: 100vh; }
            #messages { flex: 1; overflow-y: auto; padding: 12px; }
            .msg { margin-bottom: 12px; padding: 8px 12px; border-radius: 8px; font-size: 13px; line-height: 1.5; }
            .user { background: var(--vscode-inputOption-activeBackground); text-align: right; }
            .bot  { background: var(--vscode-editor-inactiveSelectionBackground); }
            #input-row { display: flex; gap: 6px; padding: 8px; border-top: 1px solid var(--vscode-widget-border); }
            #input { flex: 1; background: var(--vscode-input-background); color: var(--vscode-input-foreground);
                     border: 1px solid var(--vscode-input-border); border-radius: 4px; padding: 6px 10px;
                     font-family: var(--vscode-font-family); font-size: 13px; }
            button { background: var(--vscode-button-background); color: var(--vscode-button-foreground);
                     border: none; border-radius: 4px; padding: 6px 14px; cursor: pointer; font-size: 13px; }
            button:hover { background: var(--vscode-button-hoverBackground); }
            #toolbar { display: flex; gap: 6px; padding: 6px 8px; border-bottom: 1px solid var(--vscode-widget-border); }
            select { background: var(--vscode-dropdown-background); color: var(--vscode-dropdown-foreground);
                     border: 1px solid var(--vscode-dropdown-border); border-radius: 4px; padding: 3px 6px; font-size: 12px; }
        </style></head><body>
        <div id="toolbar">
            <select id="persona">
                <option value="default">Assistant</option>
                <option value="architect">Architect</option>
                <option value="security">Security</option>
                <option value="perf">Performance</option>
                <option value="mentor">Mentor</option>
            </select>
            <select id="mode">
                <option value="tech">Technical</option>
                <option value="plain">Plain English</option>
            </select>
        </div>
        <div id="messages"><div class="msg bot">LogOracle AI ready. Ask about your code or logs.</div></div>
        <div id="input-row">
            <input id="input" type="text" placeholder="Ask the assistant..." />
            <button onclick="send()">Send</button>
        </div>
        <script>
            const vscode = acquireVsCodeApi();
            let currentBot = null;

            document.getElementById('input').addEventListener('keydown', e => {
                if (e.key === 'Enter') send();
            });

            function send() {
                const input   = document.getElementById('input');
                const text    = input.value.trim();
                if (!text) return;
                input.value   = '';
                const msgs    = document.getElementById('messages');
                msgs.innerHTML += '<div class="msg user">' + text + '</div>';
                currentBot    = document.createElement('div');
                currentBot.className = 'msg bot';
                msgs.appendChild(currentBot);
                msgs.scrollTop = msgs.scrollHeight;

                vscode.postMessage({
                    type:    'send',
                    text,
                    persona: document.getElementById('persona').value,
                    mode:    document.getElementById('mode').value,
                });
            }

            window.addEventListener('message', e => {
                const d = e.data;
                if (d.type === 'token' && currentBot) {
                    currentBot.textContent += d.token;
                    document.getElementById('messages').scrollTop = 9999;
                } else if (d.type === 'done') {
                    currentBot = null;
                } else if (d.type === 'error') {
                    if (currentBot) currentBot.textContent = 'Error: ' + d.message;
                }
            });
        </script></body></html>`;
    }
}
exports.ChatPanel = ChatPanel;
//# sourceMappingURL=chat_panel.js.map