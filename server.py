#!/usr/bin/env python3
"""
Cod3x Web Server - Full Agent Control Panel with AI
"""

import sys, os, json, asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
cod3x_instance = None

# Keep the exact same HTML but fix the JS sendMsg function
HTML = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cod3x Agent Control Panel</title>
    <style>
        :root { --bg: #0a0a14; --panel: #12122a; --border: #2a2a4e; --accent: #7c5cff; --text: #e0e0e0; --dim: #888; --hover: #1a1a3e; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        .topbar { background: linear-gradient(135deg, #1a1a3e, #2a1a4e); padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--accent); z-index: 100; }
        .topbar h1 { font-size: 1.2em; color: var(--accent); }
        .topbar .stats { display: flex; gap: 15px; font-size: 0.7em; }
        .topbar .stats span { padding: 4px 10px; background: #1a1a3e; border-radius: 12px; }
        .topbar .dot { width: 6px; height: 6px; background: #4cff4c; border-radius: 50%; display: inline-block; margin-right: 4px; }
        .tabs { display: flex; background: #0e0e22; border-bottom: 1px solid var(--border); overflow-x: auto; scrollbar-width: none; padding: 0 10px; flex-shrink: 0; }
        .tabs::-webkit-scrollbar { display: none; }
        .tab { padding: 10px 14px; color: var(--dim); font-size: 0.78em; cursor: pointer; border-bottom: 2px solid transparent; white-space: nowrap; transition: all 0.2s; user-select: none; }
        .tab:hover { color: #fff; background: var(--hover); }
        .tab.active { color: var(--accent); border-bottom-color: var(--accent); }
        .tab .emoji { font-size: 1.1em; }
        .main { flex: 1; display: flex; overflow: hidden; min-height: 0; }
        .panel { flex: 1; display: none; flex-direction: column; overflow: hidden; height: calc(100vh - 120px); max-height: calc(100vh - 130px); }
        .panel.active { display: flex; }
        .chat-panel { flex: 1; display: flex; flex-direction: column; min-height: 0; }
        .chat-messages { flex: 1; overflow-y: scroll; -webkit-overflow-scrolling: touch; padding: 15px; display: flex; flex-direction: column; gap: 8px; }
        .msg { max-width: 85%; padding: 10px 14px; border-radius: 10px; animation: slideIn 0.3s ease; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        .msg.user { background: #2a1a4e; align-self: flex-end; }
        .msg.agent { background: #1a1a3e; align-self: flex-start; border: 1px solid #2a2a5e; }
        .msg .who { font-size: 0.65em; color: var(--accent); margin-bottom: 2px; }
        .msg.loading { background: #1a1a3e; align-self: flex-start; border: 1px dashed #3a2a5e; opacity: 0.8; }
        .msg.loading .dots { display: flex; gap: 3px; padding: 4px 0; }
        .msg.loading .dots span { width: 5px; height: 5px; background: var(--accent); border-radius: 50%; animation: bounce 1.4s infinite; }
        .msg.loading .dots span:nth-child(2) { animation-delay: 0.2s; }
        .msg.loading .dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 60%, 100% { opacity: 0.3; transform: translateY(0); } 30% { opacity: 1; transform: translateY(-6px); } }
        .agent-form { padding: 15px; background: #0e0e22; border-top: 1px solid var(--border); display: none; }
        .agent-form.active { display: block; }
        .agent-form h3 { color: var(--accent); margin-bottom: 10px; font-size: 0.9em; }
        .form-row { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
        .form-row input, .form-row select { padding: 8px 12px; background: #1a1a3e; border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-size: 0.85em; outline: none; flex: 1; min-width: 120px; }
        .form-row input:focus { border-color: var(--accent); }
        .form-row button { padding: 8px 16px; background: var(--accent); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .form-row button:hover { background: #6a4aee; }
        .chat-input { padding: 10px 15px; background: #0e0e22; border-top: 1px solid var(--border); display: flex; gap: 8px; }
        .chat-input input { flex: 1; padding: 10px 14px; background: #1a1a3e; border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 0.9em; outline: none; }
        .chat-input input:focus { border-color: var(--accent); }
        .chat-input button { padding: 10px 20px; background: var(--accent); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
        .statusbar { background: #0e0e22; padding: 6px 15px; font-size: 0.65em; color: var(--dim); display: flex; justify-content: space-between; border-top: 1px solid var(--border); }
        @media (max-width: 768px) { .tab { font-size: 0.7em; padding: 8px 10px; } .form-row { flex-direction: column; } }
    </style>
</head>
<body>
    <div class="topbar">
        <h1>🚀 Cod3x Control Panel</h1>
        <div class="stats">
            <span><span class="dot"></span> {{ agents }} Agents</span>
            <span>🔧 {{ tools }} Tools</span>
            <span>💾 {{ memory }} Memory</span>
            <span style="color:#4cff4c">🧠 AI: {{ ai_status }}</span>
        </div>
    </div>

    <div class="tabs" id="tabs">
        <div class="tab active" onclick="switchTab('chat')" data-tab="chat"><span class="emoji">💬</span> Chat</div>
        <div class="tab" onclick="switchTab('calendar')" data-tab="calendar"><span class="emoji">📅</span> Calendar</div>
        <div class="tab" onclick="switchTab('tasks')" data-tab="tasks"><span class="emoji">📝</span> Tasks</div>
        <div class="tab" onclick="switchTab('docs')" data-tab="docs"><span class="emoji">📄</span> Docs</div>
        <div class="tab" onclick="switchTab('contacts')" data-tab="contacts"><span class="emoji">👤</span> Contacts</div>
        <div class="tab" onclick="switchTab('expenses')" data-tab="expenses"><span class="emoji">💰</span> Expenses</div>
        <div class="tab" onclick="switchTab('search')" data-tab="search"><span class="emoji">🔍</span> Search</div>
        <div class="tab" onclick="switchTab('research')" data-tab="research"><span class="emoji">🔬</span> Research</div>
        <div class="tab" onclick="switchTab('crypto')" data-tab="crypto"><span class="emoji">💎</span> Crypto</div>
        <div class="tab" onclick="switchTab('travel')" data-tab="travel"><span class="emoji">✈️</span> Travel</div>
        <div class="tab" onclick="switchTab('meals')" data-tab="meals"><span class="emoji">🍳</span> Meals</div>
        <div class="tab" onclick="switchTab('content')" data-tab="content"><span class="emoji">✍️</span> Content</div>
        <div class="tab" onclick="switchTab('social')" data-tab="social"><span class="emoji">📱</span> Social</div>
        <div class="tab" onclick="switchTab('image')" data-tab="image"><span class="emoji">🎨</span> Image</div>
    </div>

    <div class="main">
        <!-- Chat Panel -->
        <div class="panel active" id="panel-chat">
            <div class="chat-panel">
                <div class="chat-messages" id="chat-msgs">
                    <div class="msg agent"><div class="who">Cod3x</div>👋 Welcome! I'm connected to AI. Chat freely or use agent tabs above.</div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'chat')">
                    <input type="text" id="chat-input" placeholder="Ask me anything..." autofocus>
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Calendar Panel -->
        <div class="panel" id="panel-calendar">
            <div class="chat-panel">
                <div class="chat-messages" id="calendar-msgs">
                    <div class="msg agent"><div class="who">📅 Calendar Agent</div>Manage your schedule - create, view, and delete events</div>
                </div>
                <div class="agent-form active">
                    <h3>📅 Schedule Event</h3>
                    <div class="form-row">
                        <input type="text" id="cal-title" placeholder="Event title">
                        <input type="date" id="cal-date">
                        <input type="time" id="cal-time" value="09:00">
                    </div>
                    <div class="form-row">
                        <input type="text" id="cal-location" placeholder="Location (optional)">
                        <input type="number" id="cal-duration" placeholder="Duration (min)" value="60">
                        <button type="button" onclick="createEvent()">Create Event</button>
                        <button type="button" onclick="listEvents()">📋 List Events</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'calendar')">
                    <input type="text" id="calendar-input" placeholder="Or type: schedule meeting tomorrow 2pm...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Tasks Panel -->
        <div class="panel" id="panel-tasks">
            <div class="chat-panel">
                <div class="chat-messages" id="tasks-msgs">
                    <div class="msg agent"><div class="who">📝 Tasks Agent</div>Create and manage your to-do list</div>
                </div>
                <div class="agent-form active">
                    <h3>📝 Add Task</h3>
                    <div class="form-row">
                        <input type="text" id="task-title" placeholder="Task description">
                        <select id="task-priority"><option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option></select>
                        <button type="button" onclick="addTask()">Add Task</button>
                        <button type="button" onclick="listTasks()">📋 My Tasks</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'tasks')">
                    <input type="text" id="tasks-input" placeholder="Or type: add task buy groceries priority high...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Docs Panel -->
        <div class="panel" id="panel-docs">
            <div class="chat-panel">
                <div class="chat-messages" id="docs-msgs">
                    <div class="msg agent"><div class="who">📄 Docs Agent</div>Create and manage your documents</div>
                </div>
                <div class="agent-form active">
                    <h3>📄 New Document</h3>
                    <div class="form-row">
                        <input type="text" id="doc-title" placeholder="Document title">
                        <select id="doc-type"><option value="note">Note</option><option value="report">Report</option><option value="guide">Guide</option></select>
                        <button type="button" onclick="createDoc()">Create</button>
                        <button type="button" onclick="listDocs()">📋 My Docs</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'docs')">
                    <input type="text" id="docs-input" placeholder="Or type: create a guide about...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Contacts Panel -->
        <div class="panel" id="panel-contacts">
            <div class="chat-panel">
                <div class="chat-messages" id="contacts-msgs">
                    <div class="msg agent"><div class="who">👤 Contacts Agent</div>Manage your contacts and address book</div>
                </div>
                <div class="agent-form active">
                    <h3>👤 Add Contact</h3>
                    <div class="form-row">
                        <input type="text" id="contact-name" placeholder="Full name">
                        <input type="email" id="contact-email" placeholder="Email address">
                        <input type="tel" id="contact-phone" placeholder="Phone number">
                        <button type="button" onclick="addContact()">Add Contact</button>
                        <button type="button" onclick="listContacts()">📋 My Contacts</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'contacts')">
                    <input type="text" id="contacts-input" placeholder="Or type: add contact John...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Expenses Panel -->
        <div class="panel" id="panel-expenses">
            <div class="chat-panel">
                <div class="chat-messages" id="expenses-msgs">
                    <div class="msg agent"><div class="who">💰 Expenses Agent</div>Track your spending and manage budgets</div>
                </div>
                <div class="agent-form active">
                    <h3>💰 Log Expense</h3>
                    <div class="form-row">
                        <input type="number" id="exp-amount" placeholder="Amount ($)" step="0.01">
                        <input type="text" id="exp-desc" placeholder="Description">
                        <select id="exp-category"><option value="food">Food</option><option value="transport">Transport</option><option value="entertainment">Entertainment</option><option value="bills">Bills</option><option value="shopping">Shopping</option><option value="other">Other</option></select>
                        <button type="button" onclick="addExpense()">Log Expense</button>
                        <button type="button" onclick="showReport()">📊 Report</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'expenses')">
                    <input type="text" id="expenses-input" placeholder="Or type: log expense $50 for lunch...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Search Panel -->
        <div class="panel" id="panel-search">
            <div class="chat-panel">
                <div class="chat-messages" id="search-msgs">
                    <div class="msg agent"><div class="who">🔍 Search Agent</div>Search the web for information - powered by AI</div>
                </div>
                <div class="agent-form active">
                    <h3>🔍 Web Search</h3>
                    <div class="form-row">
                        <input type="text" id="search-query" placeholder="Search for anything...">
                        <button type="button" onclick="doSearch()">Search</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'search')">
                    <input type="text" id="search-input" placeholder="Or type: search for latest AI news...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Research Panel -->
        <div class="panel" id="panel-research">
            <div class="chat-panel">
                <div class="chat-messages" id="research-msgs">
                    <div class="msg agent"><div class="who">🔬 Research Agent</div>Deep research and analysis on any topic</div>
                </div>
                <div class="agent-form active">
                    <h3>🔬 Research Topic</h3>
                    <div class="form-row">
                        <input type="text" id="research-topic" placeholder="What do you want to research?">
                        <select id="research-depth"><option value="brief">Brief</option><option value="detailed" selected>Detailed</option><option value="comprehensive">Comprehensive</option></select>
                        <button type="button" onclick="doResearch()">Research</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'research')">
                    <input type="text" id="research-input" placeholder="Or type: research quantum computing...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Crypto Panel -->
        <div class="panel" id="panel-crypto">
            <div class="chat-panel">
                <div class="chat-messages" id="crypto-msgs">
                    <div class="msg agent"><div class="who">💎 Crypto Agent</div>Check cryptocurrency prices and trends</div>
                </div>
                <div class="agent-form active">
                    <h3>💎 Crypto Prices</h3>
                    <div class="form-row">
                        <button type="button" onclick="cryptoPrice('bitcoin')">₿ Bitcoin</button>
                        <button type="button" onclick="cryptoPrice('ethereum')">Ξ Ethereum</button>
                        <button type="button" onclick="cryptoPrice('solana')">◎ Solana</button>
                        <button type="button" onclick="cryptoPrice('cardano')">₳ Cardano</button>
                        <button type="button" onclick="cryptoPrice('dogecoin')">Ð Dogecoin</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'crypto')">
                    <input type="text" id="crypto-input" placeholder="Or type: price of bitcoin...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Travel Panel -->
        <div class="panel" id="panel-travel">
            <div class="chat-panel">
                <div class="chat-messages" id="travel-msgs">
                    <div class="msg agent"><div class="who">✈️ Travel Agent</div>Plan your next adventure</div>
                </div>
                <div class="agent-form active">
                    <h3>✈️ Plan Trip</h3>
                    <div class="form-row">
                        <input type="text" id="trip-dest" placeholder="Destination">
                        <input type="date" id="trip-start">
                        <input type="date" id="trip-end">
                        <select id="trip-budget"><option value="budget">Budget</option><option value="moderate" selected>Moderate</option><option value="luxury">Luxury</option></select>
                        <button type="button" onclick="planTrip()">Plan Trip</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'travel')">
                    <input type="text" id="travel-input" placeholder="Or type: plan trip to Tokyo...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Meals Panel -->
        <div class="panel" id="panel-meals">
            <div class="chat-panel">
                <div class="chat-messages" id="meals-msgs">
                    <div class="msg agent"><div class="who">🍳 Meals Agent</div>Get recipes and meal suggestions</div>
                </div>
                <div class="agent-form active">
                    <h3>🍳 Recipe Finder</h3>
                    <div class="form-row">
                        <input type="text" id="meal-query" placeholder="What do you want to cook?">
                        <button type="button" onclick="getRecipe()">Get Recipe</button>
                        <button type="button" onclick="suggestMeal()">🎲 Suggest Meal</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'meals')">
                    <input type="text" id="meals-input" placeholder="Or type: recipe for ugali...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Content Panel -->
        <div class="panel" id="panel-content">
            <div class="chat-panel">
                <div class="chat-messages" id="content-msgs">
                    <div class="msg agent"><div class="who">✍️ Content Agent</div>Write articles, posts, and content</div>
                </div>
                <div class="agent-form active">
                    <h3>✍️ Create Content</h3>
                    <div class="form-row">
                        <input type="text" id="content-topic" placeholder="Topic to write about">
                        <select id="content-type"><option value="article">Article</option><option value="blog">Blog Post</option><option value="social">Social Media</option><option value="email">Email</option></select>
                        <button type="button" onclick="createContent()">Generate</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'content')">
                    <input type="text" id="content-input" placeholder="Or type: write article about AI...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Social Panel -->
        <div class="panel" id="panel-social">
            <div class="chat-panel">
                <div class="chat-messages" id="social-msgs">
                    <div class="msg agent"><div class="who">📱 Social Agent</div>Manage your social media presence</div>
                </div>
                <div class="agent-form active">
                    <h3>📱 Create Post</h3>
                    <div class="form-row">
                        <input type="text" id="social-text" placeholder="Post content...">
                        <select id="social-platform"><option value="twitter">Twitter/X</option><option value="linkedin">LinkedIn</option><option value="facebook">Facebook</option></select>
                        <button type="button" onclick="createPost()">Post</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'social')">
                    <input type="text" id="social-input" placeholder="Or type: post to twitter...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>

        <!-- Image Panel -->
        <div class="panel" id="panel-image">
            <div class="chat-panel">
                <div class="chat-messages" id="image-msgs">
                    <div class="msg agent"><div class="who">🎨 Image Agent</div>Generate and edit images with AI</div>
                </div>
                <div class="agent-form active">
                    <h3>🎨 Generate Image</h3>
                    <div class="form-row">
                        <input type="text" id="image-prompt" placeholder="Describe the image you want...">
                        <select id="image-style"><option value="realistic">Realistic</option><option value="artistic">Artistic</option><option value="cartoon">Cartoon</option><option value="abstract">Abstract</option></select>
                        <button type="button" onclick="genImage()">Generate</button>
                    </div>
                </div>
                <form class="chat-input" onsubmit="sendMsg(event, 'image')">
                    <input type="text" id="image-input" placeholder="Or type: generate image of...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>
    </div>

    <div class="statusbar">
        <span id="current-agent">💬 General Chat</span>
        <span id="msg-count">Ready</span>
    </div>

    <script>
        let currentTab = 'chat';

        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.querySelector(`[data-tab="${tab}"]`)?.classList.add('active');
            const panel = document.getElementById(`panel-${tab}`);
            if (panel) panel.classList.add('active');

            const names = {
                'chat':'💬 General Chat','calendar':'📅 Calendar Agent','tasks':'📝 Tasks Agent',
                'docs':'📄 Docs Agent','contacts':'👤 Contacts Agent','expenses':'💰 Expenses Agent',
                'search':'🔍 Search Agent','research':'🔬 Research Agent','crypto':'💎 Crypto Agent',
                'travel':'✈️ Travel Agent','meals':'🍳 Meals Agent','content':'✍️ Content Agent',
                'social':'📱 Social Agent','image':'🎨 Image Agent'
            };
            document.getElementById('current-agent').textContent = names[tab] || tab;
        }

        function addLoading(panelId) {
            const msgs = document.getElementById(panelId + '-msgs');
            if(!msgs) return;
            const div = document.createElement('div');
            div.className = 'msg loading';
            div.id = 'loading-' + panelId;
            div.innerHTML = '<div class="who">Thinking...</div><div class="dots"><span></span><span></span><span></span></div>';
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
        }

        function removeLoading(panelId, text, who) {
            const loading = document.getElementById('loading-' + panelId);
            if(loading) loading.remove();
            const msgs = document.getElementById(panelId + '-msgs');
            if(!msgs) return;
            const div = document.createElement('div');
            div.className = 'msg agent';
            div.innerHTML = `<div class="who">${who}</div>${text.replace(/\n/g, '<br>')}`;
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
            document.getElementById('msg-count').textContent = msgs.children.length + ' messages';
        }

        function addMsg(panelId, text, who) {
            const msgs = document.getElementById(panelId + '-msgs');
            if(!msgs) return;
            const div = document.createElement('div');
            div.className = 'msg ' + (who === 'You' ? 'user' : 'agent');
            div.innerHTML = `<div class="who">${who}</div>${text.replace(/\n/g, '<br>')}`;
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
        }

        async function sendMsg(e, panelId) {
            e.preventDefault();
            const input = document.getElementById(panelId + '-input');
            if(!input) return;
            const text = input.value.trim();
            if(!text) return;

            addMsg(panelId, text, 'You');
            input.value = '';
            addLoading(panelId);

            try {
                const r = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text, agent: panelId})
                });
                const d = await r.json();
                const who = panelId === 'chat' ? 'Cod3x' : panelId.charAt(0).toUpperCase() + panelId.slice(1);
                removeLoading(panelId, d.response, who);
            } catch(e) {
                removeLoading(panelId, 'Error: ' + e.message, 'System');
            }
        }

        function createEvent() {
            const title = document.getElementById('cal-title')?.value || 'Meeting';
            const date = document.getElementById('cal-date')?.value || new Date().toISOString().split('T')[0];
            const time = document.getElementById('cal-time')?.value || '09:00';
            const loc = document.getElementById('cal-location')?.value || '';
            const dur = document.getElementById('cal-duration')?.value || 60;
            const input = document.getElementById('calendar-input');
            if(input) input.value = `schedule ${title} on ${date} at ${time} for ${dur} minutes${loc ? ' at ' + loc : ''}`;
            sendMsg(new Event('submit'), 'calendar');
        }
        function listEvents() {
            const input = document.getElementById('calendar-input');
            if(input) input.value = 'list events';
            sendMsg(new Event('submit'), 'calendar');
        }
        function addTask() {
            const title = document.getElementById('task-title')?.value || 'New Task';
            const prio = document.getElementById('task-priority')?.value || 'medium';
            const input = document.getElementById('tasks-input');
            if(input) input.value = `add task ${title} priority ${prio}`;
            sendMsg(new Event('submit'), 'tasks');
        }
        function listTasks() {
            const input = document.getElementById('tasks-input');
            if(input) input.value = 'list tasks';
            sendMsg(new Event('submit'), 'tasks');
        }
        function createDoc() {
            const title = document.getElementById('doc-title')?.value || 'Untitled';
            const type = document.getElementById('doc-type')?.value || 'note';
            const input = document.getElementById('docs-input');
            if(input) input.value = `create ${type} titled ${title}`;
            sendMsg(new Event('submit'), 'docs');
        }
        function listDocs() {
            const input = document.getElementById('docs-input');
            if(input) input.value = 'list documents';
            sendMsg(new Event('submit'), 'docs');
        }
        function addContact() {
            const name = document.getElementById('contact-name')?.value || 'New Contact';
            const email = document.getElementById('contact-email')?.value || '';
            const phone = document.getElementById('contact-phone')?.value || '';
            const input = document.getElementById('contacts-input');
            if(input) input.value = `add contact ${name}${email ? ' email ' + email : ''}${phone ? ' phone ' + phone : ''}`;
            sendMsg(new Event('submit'), 'contacts');
        }
        function listContacts() {
            const input = document.getElementById('contacts-input');
            if(input) input.value = 'list contacts';
            sendMsg(new Event('submit'), 'contacts');
        }
        function addExpense() {
            const amt = document.getElementById('exp-amount')?.value;
            if(!amt) { alert('Enter amount'); return; }
            const desc = document.getElementById('exp-desc')?.value || 'item';
            const cat = document.getElementById('exp-category')?.value || 'other';
            const input = document.getElementById('expenses-input');
            if(input) input.value = `log expense $${amt} for ${desc} category ${cat}`;
            sendMsg(new Event('submit'), 'expenses');
        }
        function showReport() {
            const input = document.getElementById('expenses-input');
            if(input) input.value = 'expense report';
            sendMsg(new Event('submit'), 'expenses');
        }
        function doSearch() {
            const q = document.getElementById('search-query')?.value;
            if(!q) return;
            const input = document.getElementById('search-input');
            if(input) input.value = `search for ${q}`;
            sendMsg(new Event('submit'), 'search');
        }
        function doResearch() {
            const topic = document.getElementById('research-topic')?.value;
            if(!topic) { alert('Enter a research topic'); return; }
            const depth = document.getElementById('research-depth')?.value || 'detailed';
            const input = document.getElementById('research-input');
            if(input) input.value = `research ${topic} ${depth}`;
            sendMsg(new Event('submit'), 'research');
        }
        function cryptoPrice(coin) {
            const input = document.getElementById('crypto-input');
            if(input) input.value = `price of ${coin}`;
            sendMsg(new Event('submit'), 'crypto');
        }
        function planTrip() {
            const dest = document.getElementById('trip-dest')?.value;
            if(!dest) { alert('Enter destination'); return; }
            const start = document.getElementById('trip-start')?.value || '';
            const end = document.getElementById('trip-end')?.value || '';
            const budget = document.getElementById('trip-budget')?.value || 'moderate';
            const input = document.getElementById('travel-input');
            if(input) input.value = `plan trip to ${dest}${start ? ' from ' + start : ''}${end ? ' to ' + end : ''} budget ${budget}`;
            sendMsg(new Event('submit'), 'travel');
        }
        function getRecipe() {
            const q = document.getElementById('meal-query')?.value;
            if(!q) return;
            const input = document.getElementById('meals-input');
            if(input) input.value = `recipe for ${q}`;
            sendMsg(new Event('submit'), 'meals');
        }
        function suggestMeal() {
            const input = document.getElementById('meals-input');
            if(input) input.value = 'suggest meal';
            sendMsg(new Event('submit'), 'meals');
        }
        function createContent() {
            const topic = document.getElementById('content-topic')?.value;
            if(!topic) { alert('Enter topic'); return; }
            const type = document.getElementById('content-type')?.value || 'article';
            const input = document.getElementById('content-input');
            if(input) input.value = `write ${type} about ${topic}`;
            sendMsg(new Event('submit'), 'content');
        }
        function createPost() {
            const text = document.getElementById('social-text')?.value;
            if(!text) { alert('Enter post content'); return; }
            const platform = document.getElementById('social-platform')?.value || 'twitter';
            const input = document.getElementById('social-input');
            if(input) input.value = `post to ${platform}: ${text}`;
            sendMsg(new Event('submit'), 'social');
        }
        function genImage() {
            const prompt = document.getElementById('image-prompt')?.value;
            if(!prompt) { alert('Describe the image'); return; }
            const style = document.getElementById('image-style')?.value || 'realistic';
            const input = document.getElementById('image-input');
            if(input) input.value = `generate ${style} image of ${prompt}`;
            sendMsg(new Event('submit'), 'image');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    ai = cod3x_instance.model if cod3x_instance else None
    ai_status = "✅ Connected" if cod3x_instance and cod3x_instance.model else "⚠️ Offline"
    agents_count = len(cod3x_instance.agents) if cod3x_instance else 0
    tools_count = len(cod3x_instance.tools) if cod3x_instance else 0
    memory_count = len(cod3x_instance.memory) if cod3x_instance else 0
    return render_template_string(HTML, agents=agents_count, tools=tools_count, memory=memory_count, ai_status=ai_status)

@app.route('/chat', methods=['POST'])
def chat():
    if not cod3x_instance:
        return jsonify({'response': 'System initializing...'})
    
    data = request.get_json()
    message = data.get('message', '')
    agent_name = data.get('agent', 'chat')
    user_id = request.remote_addr or 'web_user'
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if agent_name in cod3x_instance.agents and agent_name != 'chat':
            response = loop.run_until_complete(
                cod3x_instance.agents[agent_name].process(message, user_id)
            )
        else:
            response = loop.run_until_complete(
                cod3x_instance.process_request(message, user_id)
            )
        
        loop.close()
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)[:200]}"})

def init_cod3x():
    global cod3x_instance
    from cod3x_main import Cod3xMain
    from utils.config import Config
    from utils.logger import setup_logger
    
    config = Config('config.yaml' if os.path.exists('config.yaml') else None)
    logger = setup_logger(config.get('logging', {}), False)
    
    cod3x_instance = Cod3xMain(config, logger)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cod3x_instance.initialize())
    loop.close()
    
    return cod3x_instance

if __name__ == '__main__':
    init_cod3x()
    print(f"\n🌐 Cod3x Control Panel: http://localhost:9000\n")
    app.run(host='0.0.0.0', port=9000, debug=False, use_reloader=False)
