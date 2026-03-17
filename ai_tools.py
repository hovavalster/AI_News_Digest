"""
ai_tools.py — Curated AI Tool Spotlight list for the AI News Digest.
One tool per day, rotating by date.
"""

from datetime import date

TOOLS: list[dict] = [
    {
        "name": "Cursor",
        "category": "AI Code Editor",
        "what": "An IDE built around AI — you describe what you want in plain English and it writes, edits, and refactors code across your entire project.",
        "try_this": "Open a file and press Ctrl+K. Type 'add error handling to this function' and watch it rewrite the code in place.",
        "url": "https://cursor.com",
    },
    {
        "name": "Perplexity",
        "category": "AI Search Engine",
        "what": "A search engine that actually answers your question instead of giving you 10 links — with citations so you can verify every claim.",
        "try_this": "Ask it something you'd normally Google but want a direct answer to: 'What's the best evidence on whether standing desks actually help?'",
        "url": "https://perplexity.ai",
    },
    {
        "name": "Gamma",
        "category": "AI Presentations",
        "what": "Turns a text prompt or document into a fully designed presentation in seconds — slides, layout, visuals included.",
        "try_this": "Paste in a one-paragraph idea and click Generate. You'll have a 10-slide deck in under a minute.",
        "url": "https://gamma.app",
    },
    {
        "name": "ElevenLabs",
        "category": "AI Voice",
        "what": "Converts text to incredibly realistic speech, or clones a voice from a short audio sample. Used by podcasters, filmmakers, and developers.",
        "try_this": "Paste any paragraph of text and try the free voice preview — the quality gap vs. older text-to-speech is enormous.",
        "url": "https://elevenlabs.io",
    },
    {
        "name": "Runway",
        "category": "AI Video Generation",
        "what": "Generates and edits video from text prompts or images. Used by filmmakers and content creators to create shots that would otherwise require expensive production.",
        "try_this": "Upload a photo and use the 'Image to Video' feature — describe a simple motion (e.g. 'camera slowly pulls back') and see what it does.",
        "url": "https://runwayml.com",
    },
    {
        "name": "Otter.ai",
        "category": "AI Meeting Assistant",
        "what": "Joins your Zoom, Meet, or Teams calls and produces a real-time transcript, summary, and action items automatically.",
        "try_this": "Let it run on your next meeting and compare its auto-generated summary to your own notes — most people find it catches things they missed.",
        "url": "https://otter.ai",
    },
    {
        "name": "Suno",
        "category": "AI Music Generation",
        "what": "Generates complete songs — vocals, instruments, lyrics — from a text prompt. Describe a genre and mood and it produces something that sounds like a real recording.",
        "try_this": "Type 'upbeat bossa nova about a Monday morning in Tel Aviv' and listen to what it creates in 30 seconds.",
        "url": "https://suno.com",
    },
    {
        "name": "v0 by Vercel",
        "category": "AI UI Builder",
        "what": "Describe a web interface in plain English and it generates the actual code — React components, styled and ready to use.",
        "try_this": "Type 'a dashboard with a sidebar, a chart of monthly revenue, and a recent transactions table' and it builds the UI instantly.",
        "url": "https://v0.dev",
    },
    {
        "name": "Bolt.new",
        "category": "AI App Builder",
        "what": "Build full web apps from a text description — frontend, backend, and database — directly in the browser without any setup.",
        "try_this": "Describe a simple app: 'a to-do list that saves to a database and lets me filter by priority.' It scaffolds the whole thing.",
        "url": "https://bolt.new",
    },
    {
        "name": "Descript",
        "category": "AI Podcast & Video Editor",
        "what": "Edit audio and video by editing the transcript — delete a word from the text and it removes it from the recording. Also removes filler words automatically.",
        "try_this": "Record yourself talking for 2 minutes, upload it, and use 'Remove filler words' — the difference is striking.",
        "url": "https://descript.com",
    },
    {
        "name": "HeyGen",
        "category": "AI Video Avatars",
        "what": "Create a video of a realistic AI avatar speaking your script — used for training videos, product demos, and multilingual content.",
        "try_this": "Use the free tier to create a 30-second video with one of their stock avatars — you'll immediately see the use case for repeatable video content.",
        "url": "https://heygen.com",
    },
    {
        "name": "Groq",
        "category": "Ultra-Fast AI Inference",
        "what": "Runs open-source LLMs (Llama, Mistral, etc.) at speeds that feel instant — responses in under a second, even for complex queries.",
        "try_this": "Go to groq.com/playground and ask it a multi-step reasoning question. The speed difference vs. other services is immediately obvious.",
        "url": "https://groq.com",
    },
    {
        "name": "Ollama",
        "category": "Local AI Models",
        "what": "Run powerful AI models (Llama 3, Mistral, Phi) entirely on your own laptop — no internet, no API costs, no data leaving your machine.",
        "try_this": "Install it and run 'ollama run llama3.2' in your terminal. You now have a capable local AI with complete privacy.",
        "url": "https://ollama.com",
    },
    {
        "name": "LM Studio",
        "category": "Local AI Models",
        "what": "A desktop app for running open-source AI models locally, with a clean chat interface and a built-in model library to browse and download.",
        "try_this": "Download Phi-3 Mini (only 2GB) and run it — it's surprisingly capable for summarization and Q&A on a normal laptop.",
        "url": "https://lmstudio.ai",
    },
    {
        "name": "n8n",
        "category": "AI Workflow Automation",
        "what": "An open-source automation tool that connects apps and AI models in visual workflows — like Zapier but with full control and AI built in.",
        "try_this": "Create a workflow: 'When I receive an email with an attachment, summarize it with Claude and send me a Slack message.' No code required.",
        "url": "https://n8n.io",
    },
    {
        "name": "Replit",
        "category": "AI-Powered Cloud IDE",
        "what": "A browser-based coding environment where you can build and deploy apps without any local setup — now with an AI agent that writes and fixes code for you.",
        "try_this": "Open replit.com, click 'Create with AI', and describe a simple app. It builds, runs, and hosts it for you in one place.",
        "url": "https://replit.com",
    },
    {
        "name": "Windsurf",
        "category": "AI Code Editor",
        "what": "Codeium's AI-native IDE — similar to Cursor, with an 'Agentic' mode called Cascade that can plan and execute multi-step coding tasks across your project.",
        "try_this": "Open a project and use Cascade to ask it to 'add dark mode support' — it figures out which files to touch and makes all the changes.",
        "url": "https://codeium.com/windsurf",
    },
    {
        "name": "Mistral Le Chat",
        "category": "AI Assistant",
        "what": "Mistral's chat interface for their frontier models — fast, private-focused, with strong reasoning and multilingual capabilities. Often overlooked next to ChatGPT.",
        "try_this": "Try asking it something in Hebrew or French — Mistral's multilingual performance is genuinely strong compared to many alternatives.",
        "url": "https://chat.mistral.ai",
    },
    {
        "name": "OpenRouter",
        "category": "AI Model Router",
        "what": "A single API that gives you access to 100+ AI models (Claude, GPT-4, Llama, Gemini) through one interface — useful for comparing models or building apps.",
        "try_this": "Send the same prompt to three different models side-by-side and compare — it's eye-opening how differently they respond to identical inputs.",
        "url": "https://openrouter.ai",
    },
    {
        "name": "Weights & Biases",
        "category": "AI Experiment Tracking",
        "what": "Tracks your AI experiments, model training runs, and evaluations — the standard tool professionals use to understand why a model behaves the way it does.",
        "try_this": "Even if you don't train models, their free 'Weave' product lets you log and compare Claude/GPT prompts and outputs across versions.",
        "url": "https://wandb.ai",
    },
    {
        "name": "Hugging Face",
        "category": "AI Model Hub",
        "what": "The GitHub of AI models — 500,000+ models, datasets, and demos available for free. Where researchers publish new models before anywhere else.",
        "try_this": "Go to huggingface.co/spaces and search for any task (e.g. 'background removal') — you'll find free browser-based demos instantly.",
        "url": "https://huggingface.co",
    },
    {
        "name": "Replicate",
        "category": "AI Model API",
        "what": "Run any open-source AI model via API without managing infrastructure — image generation, video, audio, code, all accessible with a few lines of code.",
        "try_this": "Use their Explore page to find an image model you've heard of (SDXL, Flux) and run it directly in the browser with no signup.",
        "url": "https://replicate.com",
    },
    {
        "name": "Pika",
        "category": "AI Video Generation",
        "what": "Generate short videos from text prompts or images — specializes in stylized, cinematic clips. Popular with creators making social content.",
        "try_this": "Upload any photo and use the 'Animate' feature with a simple motion description — even basic inputs produce surprisingly polished results.",
        "url": "https://pika.art",
    },
    {
        "name": "Aider",
        "category": "AI Terminal Coding Assistant",
        "what": "A command-line AI coding assistant that works directly with your local git repo — you chat with it in your terminal and it commits changes as it goes.",
        "try_this": "Run 'aider --model claude-sonnet-4-6' in any project folder and ask it to 'add a README.md explaining what this project does.'",
        "url": "https://aider.chat",
    },
    {
        "name": "Notion AI",
        "category": "AI in Your Workspace",
        "what": "AI built directly into Notion — summarizes pages, rewrites text, answers questions about your documents, and auto-fills databases.",
        "try_this": "In any Notion page, type /AI and ask it to 'summarize this page into 5 bullet points' — it reads the whole document and responds in seconds.",
        "url": "https://notion.so/product/ai",
    },
    {
        "name": "Napkin AI",
        "category": "AI Visual Thinking",
        "what": "Paste any text and it automatically generates diagrams, flowcharts, and visual summaries — great for turning reports or meeting notes into shareable visuals.",
        "try_this": "Paste a paragraph describing any process or framework and see it converted into a professional diagram you can export.",
        "url": "https://napkin.ai",
    },
    {
        "name": "Ideogram",
        "category": "AI Image Generation",
        "what": "An image generator that actually gets text right — one of the few AI image tools that can reliably render readable words inside images.",
        "try_this": "Generate a poster with specific text in it (something most other image AIs fail at badly) and compare the result to what Midjourney would produce.",
        "url": "https://ideogram.ai",
    },
    {
        "name": "Granola",
        "category": "AI Meeting Notes",
        "what": "A Mac app that captures your meetings locally (no bot joining the call) and enhances your rough notes with AI — private and lightweight.",
        "try_this": "Let it run during any internal meeting — it combines your sparse notes with the audio to produce structured, readable summaries.",
        "url": "https://granola.so",
    },
    {
        "name": "Together AI",
        "category": "Fast Open-Source AI API",
        "what": "API access to leading open-source models (Llama, Mistral, DBRX) at very low cost and high speed — popular with developers building AI products.",
        "try_this": "Their free playground lets you compare Llama 3 70B vs. Mistral Large on the same prompt — useful for deciding which model to build on.",
        "url": "https://together.ai",
    },
    {
        "name": "Voiceflow",
        "category": "AI Agent Builder",
        "what": "A no-code platform for building AI-powered chatbots and voice agents — used by companies to build customer service automation without engineering.",
        "try_this": "Use their template library to deploy a basic FAQ chatbot in 10 minutes and see how far no-code AI agents have come.",
        "url": "https://voiceflow.com",
    },
]


def pick_tool_of_the_day() -> dict:
    """Returns one tool deterministically based on today's date."""
    idx = date.today().timetuple().tm_yday
    return TOOLS[idx % len(TOOLS)]
