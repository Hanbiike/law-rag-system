## 🔒 Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| < 1.0   | :x:                |

## 🚨 Reporting a Vulnerability

We take the security of Law RAG System seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

**Please DO NOT open a public issue for security vulnerabilities.**

Instead, report vulnerabilities privately:

1. **Email:** Send details to [hanbiike.corp@gmail.com](mailto:hanbiike.corp@gmail.com)
2. **Subject Line:** Use "SECURITY: [Brief Description]"
3. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)
   - Your contact information (for follow-up)

### What to Expect

- **Acknowledgment:** Within 48 hours of your report
- **Initial Assessment:** Within 5 business days
- **Status Updates:** Every 7 days until resolved
- **Resolution:** We aim to patch critical vulnerabilities within 30 days

### Security Bug Bounty

Currently, we do not offer a paid bug bounty program. However, we deeply appreciate security researchers' contributions and will:

- Publicly acknowledge your responsible disclosure (with your permission)
- Credit you in release notes
- Provide a letter of recognition upon request

## 🛡️ Security Best Practices

### For Users

#### Environment Variables

```bash
# ⚠️ NEVER commit .env to version control
echo ".env" >> .gitignore

# Use strong, unique API keys
AZURE_OPENAI_API_KEY_NANO=your_secret_key_here
```

#### Database Security

- Use **strong passwords** for MySQL
- Restrict database access to `localhost` in production
- Enable MySQL SSL/TLS connections
- Regularly update database credentials

#### Telegram Bot

- Keep `TELEGRAM_BOT_TOKEN` private
- Use Telegram's webhook mode with HTTPS in production
- Implement rate limiting for bot requests
- Monitor unusual activity patterns

#### File Handling

- **Document size limits** are enforced:
  - PDF: max 20 MB (see `MAX_DOC_SIZE`)
  - Images: max 10 MB (see `MAX_IMAGE_SIZE`)
- **Supported formats only:** PDF, JPEG, PNG, GIF, WebP
- Files are processed via URL (no local storage)
- Azure OpenAI handles file validation

### For Developers

#### Code Security

```python
# ✅ Use environment variables
import os
api_key = os.getenv('AZURE_OPENAI_API_KEY_NANO')

# ❌ Never hardcode secrets
api_key = "sk-..."  # NEVER DO THIS
```

#### Dependencies

```bash
# Regularly update dependencies
pip install --upgrade -r requirements.txt

# Check for known vulnerabilities
pip install safety
safety check
```

#### Input Validation

- All user inputs are validated in handlers.py
- File types are restricted (see `SUPPORTED_IMAGE_TYPES`)
- Message length is limited (see `MAX_MESSAGE_LENGTH`)
- SQL queries use parameterized statements in db.py

#### Authentication & Authorization

- User data is stored securely in MySQL (see `databases/db.py`)
- Balance verification prevents abuse (see `user_repository.deduct_balance`)
- Rate limiting via balance system

## 🔐 Known Security Considerations

### Azure OpenAI API Keys

- **Risk:** Exposed API keys can lead to unauthorized usage
- **Mitigation:** 
  - Store in .env (gitignored)
  - Use Azure Key Vault in production
  - Enable API key rotation
  - Monitor usage in Azure Portal

### MySQL Database

- **Risk:** SQL injection, unauthorized access
- **Mitigation:**
  - Parameterized queries (see `databases/db.py`)
  - Restricted network access
  - Strong passwords
  - Regular backups

### Milvus Vector Database

- **Risk:** Data exposure if milvus_law_rag.db is publicly accessible
- **Mitigation:**
  - Store in secure location
  - Restrict file permissions (chmod 600)
  - No sensitive personal data stored

### User Balance System

- **Risk:** Balance manipulation
- **Mitigation:**
  - Server-side validation only
  - Atomic database transactions
  - Cost verification in handlers.py

### Document Processing

- **Risk:** Malicious files, injection attacks
- **Mitigation:**
  - File size limits enforced
  - Format validation
  - Azure OpenAI handles parsing (sandboxed)
  - No local file storage

## 📋 Security Checklist for Deployment

- [ ] .env is gitignored and secured
- [ ] MySQL uses strong password (16+ characters)
- [ ] Database accessible only from localhost
- [ ] Azure OpenAI API key is rotated regularly
- [ ] Telegram bot token is kept private
- [ ] File permissions are restrictive (chmod 600 for sensitive files)
- [ ] Dependencies are up to date
- [ ] Logs are monitored for suspicious activity
- [ ] Backups are encrypted and tested
- [ ] Rate limiting is configured

## 🔄 Security Update Process

1. **Vulnerability Reported** → Acknowledged within 48 hours
2. **Assessment** → Severity assigned (Critical, High, Medium, Low)
3. **Patch Development** → Fix created and tested
4. **Security Advisory** → Published (if applicable)
5. **Release** → Patched version released
6. **Notification** → Users notified via GitHub releases
7. **Disclosure** → Full disclosure after patch deployment

## 📞 Security Contact

- **Email:** hanbiike.corp@gmail.com
- **Response Time:** 48 hours for acknowledgment
- **PGP Key:** Available upon request

## 🙏 Acknowledgments

We thank the following security researchers for responsible disclosure:

*(List will be maintained as contributions are made)*

---

**Last Updated:** January 2025

**Note:** This security policy applies to the [Law RAG System](https://github.com/Hanbiike/law-rag-system) repository and all associated components (bot, databases, aitools, parser, `searchers/`).
