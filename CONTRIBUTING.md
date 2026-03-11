# Contributing to CareAgent OS

Thank you for your interest in contributing to CareAgent OS.

## Development Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Code Style

- **Python**: Follow PEP 8. Use type hints where possible.
- **TypeScript**: Use strict mode. Prefer `const` over `let`.
- **Commits**: Use conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request with a clear description

## Architecture

See [README.md](README.md) for system architecture details.

## Agent Development

Each agent extends `BaseAgent` and must implement:
- `can_handle(task_type: str) -> bool`
- `process(input_data: dict) -> dict`

See `backend/app/agents/base_agent.py` for the interface.
