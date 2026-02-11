# Code Checkpoint 🚀

**Code Checkpoint** is an AI-powered agentic workflow designed to eliminate "context switching tax" and radically reduce onboarding time for developers. It automatically maintains a living history of your codebase, generating distinct summaries for new joiners and returning developers.

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)

## 🌟 Features

### 1. The Map (Master Context)
A "Master Context" document that evolves with every commit. Perfect for **New Joinees**.
- **Architectural Overview**: High-level system design.
- **Key Decision Log**: Why specific technical choices were made.
- **Dependency Map**: How modules interact.
- **Gotchas**: Known issues and tech debt.

**Generated at**: `MASTER_CONTEXT.md` (Repo Root)

### 2. The News Feed (Personalized Catchup)
A personalized "While You Were Gone" summary for **Returning Developers**.
- **Personalized Delta**: Scans your git history to find when you last contributed.
- **Summarized Changes**: Tells you exactly what changed since *you* left.
- **Current Focus**: What the team is working on right now.

**Generated at**: `checkpoints/Checkpoint_<YourName>.md`

## 🛠️ Usage

### Prerequisites
- Python 3.10+
- Mistral API Key

### Setup
1. Clone the repo.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your API Key in a `.env` file:
   ```env
   MISTRAL_API_KEY=your_api_key_here
   ```

### Commands

**Generate the Master Context (The Map):**
```bash
python3 main.py --onboard
```

**Get Your Personal Catchup (The News Feed):**
```bash
python3 main.py --catchup
```
*(Automatically detects your email from git config)*

**Manual Checkpoints (Optional):**
```bash
python3 main.py --commit <hash>
```

## 🤖 CI/CD Automation
This project includes a GitHub Action (`.github/workflows/checkpoint.yml`) that automatically:
1. Updates `MASTER_CONTEXT.md` on every push.
2. Generates personalized Catchup summaries for all active developers.

## 📂 Project Structure
```
.
├── main.py                 # Entry point
├── src/
│   ├── agents.py           # DSPy Agents (Generator, Synthesizer)
│   ├── graph.py            # LangGraph Workflow
│   ├── llm.py              # Mistral Provider & Configuration
│   ├── git_utils.py        # Git interactions
│   └── storage.py          # File persistence
├── checkpoints/            # Storage for generated summaries
└── MASTER_CONTEXT.md       # The Living Map
```
