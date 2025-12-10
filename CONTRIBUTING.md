Thank you for your interest in contributing to the Law RAG System! This document provides guidelines for contributing to the project.

## 🎯 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, dependencies)
- **Error messages** and stack traces
- **Screenshots** if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Use case** - why this feature would be useful
- **Detailed description** of the proposed functionality
- **Possible implementation** approach (if you have ideas)
- **Alternatives considered**

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the code style** - use existing code as a guide
3. **Add tests** if applicable
4. **Update documentation** - README, docstrings, comments
5. **Write clear commit messages** - describe what and why
6. **Ensure all tests pass** before submitting

#### Code Style Guidelines

- Follow **PEP 8** for Python code
- Use **type hints** where appropriate
- Write **descriptive docstrings** for functions and classes
- Keep functions **focused and single-purpose**
- Add **comments** for complex logic
- Use **meaningful variable names**

#### Commit Message Format

```
type: brief description

Detailed explanation of changes (if needed)

Fixes #issue-number (if applicable)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🔧 Development Setup

1. **Clone your fork:**
```bash
git clone https://github.com/your-username/law-rag-system.git
cd law-rag-system
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure .env** - see README.md

5. **Create a branch:**
```bash
git checkout -b feature/your-feature-name
```

## 📝 Areas for Contribution

### High Priority

- [ ] Redis caching implementation for LLM responses
- [ ] Web interface using FastAPI
- [ ] DOCX document upload support
- [ ] A/B testing framework for different models
- [ ] Usage statistics dashboard
- [ ] Multi-language support expansion (Uzbek, Kazakh)

### Code Quality

- [ ] Additional unit tests for aitools
- [ ] Integration tests for searchers
- [ ] Performance benchmarking scripts
- [ ] Code coverage improvements

### Documentation

- [ ] API documentation using Sphinx
- [ ] Video tutorials for setup
- [ ] More code examples in README.md
- [ ] Troubleshooting guide expansion

### Parser Improvements

- [ ] Support for additional document formats (RTF, TXT)
- [ ] Enhanced pattern recognition in document_parser.py
- [ ] Multi-document processing optimization

## 🧪 Testing

Before submitting a pull request:

1. **Test your changes** thoroughly
2. **Run existing tests** (if available)
3. **Test with both languages** (Russian and Kyrgyz)
4. **Verify Telegram bot** functionality if applicable

## 📋 Project Structure Reference

When contributing, familiarize yourself with:

- aitools - AI components (embedder, LLM)
- bot - Telegram bot implementation
- confs - Configuration management
- databases - Database operations (MySQL, Milvus)
- parser - Document parsing pipeline
- searchers - RAG search implementation

## 🤝 Code Review Process

1. **Maintainer review** - at least one maintainer must approve
2. **CI checks** must pass (when implemented)
3. **Address feedback** - respond to comments and make requested changes
4. **Merge** - maintainer will merge when ready

## 📜 License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0.

## 💬 Questions?

- Open an issue for questions about contributing
- Email: hanbiike.corp@gmail.com
- Follow the Code of Conduct

## 🙏 Recognition

Contributors will be recognized in:
- GitHub contributors page
- Project documentation
- Release notes

---

**Thank you for contributing to Law RAG System!** 🎉
