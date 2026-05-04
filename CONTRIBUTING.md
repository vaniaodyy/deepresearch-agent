# Contributing to DeepResearch Agent

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## 🚀 Getting Started

1. **Fork** the repository
2. **Clone** your fork locally
3. **Install** dependencies: `pip install -e .`
4. **Create** a branch for your feature
5. **Make** your changes
6. **Test** your changes
7. **Submit** a pull request

## 📋 Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/deepresearch-agent.git
cd deepresearch-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy deepresearch/
```

## 🎯 Areas for Contribution

### High Priority
- **Source Providers** - Add new research sources (LinkedIn, Twitter, etc.)
- **LLM Providers** - Add support for more LLM providers
- **Language Support** - Improve multilingual research capabilities
- **Testing** - Increase test coverage

### Medium Priority
- **UI/Web Dashboard** - Build a web interface
- **Caching** - Implement smart caching for faster research
- **Export Formats** - Add PDF, DOCX export
- **Scheduling** - Add scheduled research tasks

### Low Priority
- **Documentation** - Improve docs and examples
- **Performance** - Optimize search and analysis
- **Monitoring** - Add metrics and logging

## 📝 Code Style

We use:
- **Python 3.10+** features
- **Ruff** for linting
- **mypy** for type checking
- **Black** for formatting (optional)

```bash
# Format code
ruff format .

# Check style
ruff check .

# Type check
mypy deepresearch/
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=deepresearch

# Run specific test
pytest tests/test_engine.py
```

## 📚 Documentation

- Update README.md for new features
- Add docstrings to all public functions
- Update API documentation if endpoints change
- Add examples for new functionality

## 🐛 Bug Reports

When filing a bug report, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages/logs

## ✨ Feature Requests

For feature requests, please include:
- Clear description of the feature
- Use case / why it's needed
- Proposed implementation (if any)
- Alternatives considered

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Every contribution helps make DeepResearch Agent better for everyone. Thank you for your support!
