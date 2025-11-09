# GitHub Maintainer AI Agent

An autonomous AI agent system that helps maintain GitHub repositories by automatically analyzing issues, suggesting code improvements, and creating pull requests.

## Features

- Automated issue analysis and prioritization
- Code context analysis and improvement suggestions
- Automated patch generation and testing
- Pull request creation with detailed descriptions
- Memory system for learning from past actions

## Project Structure

```
github-maintainer-ai/
├── main.py                            # entrypoint for running all agents
├── requirements.txt                   # Python dependencies
├── .env.example                       # example environment variables
│
├── agents/                            # all sub-agents live here
│   ├── issue_reader.py               # reads and summarizes GitHub issues
│   ├── code_analyzer.py              # analyzes code context from repo
│   ├── patch_planner.py              # generates patch / diff suggestions
│   ├── pr_creator.py                 # creates commits + pull requests
│
├── core/                             # shared logic / utils / api clients
│   ├── github_client.py              # handles GitHub API requests
│   ├── local_model.py                # connects to Ollama / local LLM
│   ├── file_utils.py                 # helper for reading/writing files
│   ├── logger.py                     # loguru-based logging
│
├── memory/                           # stores agent memory (JSON logs)
│   ├── issues.json                   # tracked issues
│   ├── actions.json                  # performed actions
│   ├── diffs.json                    # generated diffs
│   ├── lessons.json                  # learned lessons
│
└── config/                           # configuration and environment setup
    └── settings.py                   # loads .env and global configs
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your configuration:
   ```bash
   cp .env.example .env
   ```

## Configuration

Required environment variables:
- `GITHUB_TOKEN`: Your GitHub personal access token
- `GITHUB_USERNAME`: Your GitHub username
- `REPO_OWNER`: Target repository owner
- `REPO_NAME`: Target repository name

Optional configurations:
- `OLLAMA_HOST`: Local LLM host (default: http://localhost:11434)
- `MODEL_NAME`: Local LLM model name (default: codellama)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FILE`: Log file path (default: github_maintainer.log)
- `MEMORY_DIR`: Directory for storing memory files (default: ./memory)

## Usage

Run the main agent:
```bash
python main.py
```

## Components

### Agents

- **Issue Reader**: Analyzes and prioritizes GitHub issues
- **Code Analyzer**: Provides code context and improvement suggestions
- **Patch Planner**: Plans and generates code changes
- **PR Creator**: Creates and manages pull requests

### Core Utilities

- **GitHub Client**: Handles all GitHub API interactions
- **Local Model**: Manages interactions with the local LLM
- **File Utils**: Handles file operations and memory storage
- **Logger**: Provides structured logging

### Memory System

Stores and manages:
- Tracked issues
- Performed actions
- Generated diffs
- Learned lessons

## License

MIT
