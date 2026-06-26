# Contributing to Traffic Bot

We welcome contributions from the community! Whether you want to add new features, fix bugs, improve documentation, or suggest enhancements, please follow the guidelines below.

## How to Contribute

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch** for your feature or fix (`git checkout -b feature/amazing-feature`)
4. **Make your changes** and test them
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Open a Pull Request** against the `main` branch

## Development Setup

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/traffic-bot.git
cd traffic-bot

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep functions focused and modular

## Reporting Issues

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Any error messages or logs

## Feature Requests

Feature requests are welcome! Please open an issue with:

- A clear description of the feature
- Use case / motivation
- Any implementation ideas you may have

Thank you for contributing!
