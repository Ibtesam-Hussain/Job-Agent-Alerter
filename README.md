<div align="center">

<img src="assets/banner.png" alt="JobAgent Banner" width="100%" />

<h1>JobAgent</h1>

<p><strong>Autonomous AI agent that monitors selective company career pages, reasons over job listings with an LLM, and delivers personalized alerts straight to your WhatsApp.</strong></p>

<p>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://playwright.dev/"><img src="https://img.shields.io/badge/Playwright-2EAD33?logo=playwright&logoColor=white" alt="Playwright" /></a>
  <a href="https://www.crummy.com/software/BeautifulSoup/"><img src="https://img.shields.io/badge/BeautifulSoup-FFD43B?logo=python&logoColor=black" alt="BeautifulSoup" /></a>
  <a href="https://openrouter.ai/docs"><img src="https://img.shields.io/badge/OpenRouter-6B4FBB?logo=openai&logoColor=white" alt="OpenRouter API" /></a>
  <a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white" alt="SQLite" /></a>
  <a href="https://www.json.org/"><img src="https://img.shields.io/badge/JSON-000000?logo=json&logoColor=white" alt="JSON" /></a>
  <a href="https://www.twilio.com/docs"><img src="https://img.shields.io/badge/Twilio-F22F46?logo=twilio&logoColor=white" alt="Twilio" /></a>
  <a href="https://developers.facebook.com/docs/whatsapp/"><img src="https://img.shields.io/badge/WhatsApp%20API-25D366?logo=whatsapp&logoColor=white" alt="WhatsApp API" /></a>
</p>

<p>
  <a href="#-demo">Demo</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quickstart">Quickstart</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

</div>

---

## What is JobAgent?

Most job seekers target **specific companies**, not generic job boards. But manually checking 10+ career pages every day is tedious, error-prone, and unsustainable.

**JobAgent** solves this with an autonomous agentic AI loop:

1. **Observes** company career portals via automated browser
2. **Remembers** every job it has seen — no duplicate alerts, ever
3. **Reasons** over new listings using an LLM matched against your preferences
4. **Acts** by pushing a concise WhatsApp alert with role, match reason, and apply link

It's not a scraper. It's not a chatbot. It's an **autonomous AI agent** that works for you while you sleep.

---

## Features

- 🤖 **Agentic workflow** — observe, remember, reason, act — no manual steps
- 🧠 **LLM-powered relevance scoring** — goes beyond keyword matching; understands context
- 🔕 **Zero duplicate alerts** — SQLite deduplication across all runs
- 📲 **WhatsApp notifications** — instant mobile alerts via Twilio
- 🕸️ **Dynamic page scraping** — Playwright handles JavaScript-heavy career portals
- ⚙️ **Preference-driven filtering** — roles, tech stack, location, experience level, work mode
- 💸 **Runs for free** — uses free-tier LLMs, Twilio Sandbox, and GitHub Actions
- 📦 **Open-source & self-hosted** — fork, configure, deploy in minutes
- 🗂️ **Structured logging** — `app.log` + `error.log` for full observability

---

## Architecture

```
User Preferences (user_preferences.json)
           │
           ▼
  Company Career Pages
           │
           ▼
  ┌─────────────────────┐
  │  Playwright Scraper │  ← dynamic JS rendering
  └─────────────────────┘
           │
           ▼
  ┌─────────────────────┐
  │  BeautifulSoup      │  ← HTML → clean text
  │  Parser             │
  └─────────────────────┘
           │
           ▼
  ┌─────────────────────┐
  │  Keyword Filter     │  ← removes non-technical roles
  └─────────────────────┘
           │
           ▼
  ┌─────────────────────┐
  │  Deduplication      │  ← checks scraped_jobs.db
  │  Engine             │
  └─────────────────────┘
           │  (only new jobs)
           ▼
  ┌─────────────────────┐
  │  LLM Decision       │  ← OpenRouter API
  │  Engine             │    returns { selected, score, reason }
  └─────────────────────┘
           │  (approved jobs)
           ▼
  ┌─────────────────────┐
  │  selected_jobs.db   │
  └─────────────────────┘
           │
           ▼
  ┌─────────────────────┐
  │  Twilio WhatsApp    │  ← alert sent to your phone
  │  Notifier           │
  └─────────────────────┘
```

The pipeline is **incremental** — only newly observed jobs are processed each run, keeping LLM token usage and cost minimal.

To view more detailed architecture. Please refer to `indepth-sys-architecture.png`
---

## ⚡ Quickstart

### Prerequisites

- Python 3.10+
- A [Twilio](https://www.twilio.com/) account (Sandbox is free)
- An [OpenRouter](https://openrouter.ai/) API key (free-tier models available)

### 1. Clone the repo

```bash
git clone https://github.com/Ibtesam-Hussain/Job-Agent-Alerter
cd Job Agent Alerter/
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENROUTER_API_KEY=your_openrouter_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_TO=whatsapp:+92XXXXXXXXXX
```

### 4. Configure your preferences

Edit `user_preferences.json`:

```json
{
  "target_roles": ["QA Engineer", "SQA Engineer", "Automation Tester"],
  "skills": ["selenium", "python", "api testing"],
  "experience_level": "entry-level",
  "work_mode": ["remote", "hybrid"],
  "target_companies": ["Folio3", "Systems Limited", "Tkxel"]
}
```

### 5. Run

```bash
python main.py
```

You'll receive a WhatsApp message for every matched job, like:

```
🚀 New Job Match — JobAgent

Role: Senior SQA Engineer
Company: Folio3
Match Score: 8/10
Why: Selenium + API Testing + Python alignment

Apply → https://folio3.com/careers/sqa-engineer
```

---

## Configuration

| Parameter | Description | Example |
|---|---|---|
| `target_roles` | Job titles the agent looks for | `["QA Engineer", "SDET"]` |
| `skills` | Your tech stack keywords | `["selenium", "python"]` |
| `experience_level` | Filters by seniority | `"entry-level"` |
| `work_mode` | Location preference | `["remote", "hybrid"]` |
| `target_companies` | Career pages to monitor | `["Folio3", "Tkxel"]` |

Target company career page URLs are defined in `targets.json`. Add any company by URL — the scraper handles the rest.

---

## Deployment

### Local (recommended to start)

Run manually or schedule with cron:

```bash
# Every Monday, Wednesday, Friday at 9AM
0 9 * * 1,3,5 cd /path/to/jobagent && python main.py
```


### Cloud (VPS / Railway / Render) - Optional

Deploy on any Linux VPS or platform-as-a-service. Estimated cost: **$5–10/month** for hosting; LLM and Twilio usage is near-zero for personal monitoring.

---

## 📂 Project Structure

```
.
├── main.py
├── agent/
│   ├── agent_loop.py
│   ├── decision_engine.py
│   └── LLM.txt
├── config/
│   ├── agentConfigs.txt
│   ├── user_preference.example.json
│   └── user_preferences.json
├── logs/
├── memory/
│   ├── job_database.py
│   └── user_pref_database.py
├── notifier/
│   ├── alert_service.py
│   ├── alert.txt
│   └── whatsapp_sender.py
├── scrapper/
│   ├── auto_scrapper.py
│   ├── config_manager.py
│   ├── file_utils.py
│   ├── html_parser.py
│   ├── job_extractor.py
│   ├── job_filter.py
│   ├── job-role-keywords.txt
│   ├── scraper.py
│   └── sites_configs.py
├── utils/
│   ├── discover_job_selectors.py
│   ├── logger.py
│   ├── preferences_loader.py
│   └── test_url_reachability.py
├── .gitgnore
├── development-journey.md
├── project-plan.txt
├── README.md
├── requirements.txt
└── test_urls.py
```

---

## Roadmap

- [☑️] Playwright-based dynamic scraping
- [☑️] LLM-powered job relevance scoring
- [☑️] SQLite deduplication memory
- [☑️] WhatsApp alerts via Twilio
- [☑️] GitHub Actions scheduled deployment
- [ ] Resume-to-JD semantic matching
- [ ] Telegram & Email notification channels
- [ ] Interactive dashboard (job history, scores, analytics)
- [ ] Multi-user SaaS architecture
- [ ] Auto cover letter generation
- [ ] RAG-based full JD semantic analysis
- [ ] Feedback-driven preference learning

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

---

## 👥 Authors

Built by students of the Department of Artificial Intelligence, FAST-NUCES Karachi.

| Name | GitHub |
|---|---|
| Ibtesam Hussain | [@ibtesam](https://github.com/Ibtesam-Hussain) |
| Safey Ahmed | [@safey](https://github.com/Safey-Ahmed-Suhail) |
| Zaheer Ahmed | [@zaheer](https://github.com/zaheer) |

---

<div align="center">
  <sub>If JobAgent saved you from missing a job, give it a ⭐</sub>
</div>