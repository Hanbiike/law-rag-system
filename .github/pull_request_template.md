## Description

<!-- Provide a clear and concise description of what this PR does -->

## Type of Change

<!-- Please check the one that applies to this PR using "x" -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🎨 Code style update (formatting, renaming)
- [ ] ♻️ Refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] ✅ Test update
- [ ] 🔧 Configuration change
- [ ] 🗑️ Deprecation or removal

## Related Issues

<!-- Link to the issue(s) this PR addresses -->

Fixes #(issue number)
Closes #(issue number)
Relates to #(issue number)

## Changes Made

<!-- List the specific changes made in this PR -->

- 
- 
- 

## Component(s) Affected

<!-- Check all that apply -->

- [ ] `aitools/` - AI tools (embedder, LLM)
- [ ] `bot/` - Telegram bot
- [ ] `confs/` - Configuration
- [ ] `databases/` - Database operations (MySQL, Milvus)
- [ ] `parser/` - Document parsing
- [ ] `searchers/` - Search logic
- [ ] Documentation
- [ ] Tests
- [ ] CI/CD
- [ ] Other: _____________

## Testing

<!-- Describe the tests you ran to verify your changes -->

### Test Configuration

- **Python version:** 
- **OS:** 
- **Database:** MySQL / Milvus

### Tests Performed

- [ ] Tested with Russian documents
- [ ] Tested with Kyrgyz documents
- [ ] Tested Telegram bot functionality
- [ ] Tested programmatic API
- [ ] Tested with base mode
- [ ] Tested with pro mode
- [ ] Tested with search mode
- [ ] Tested document processing (PDF)
- [ ] Tested image processing
- [ ] Manual testing performed
- [ ] Unit tests pass
- [ ] Integration tests pass

### Test Results

<!-- Paste test output or describe results -->

```
# Test output here
```

## Screenshots/Demo

<!-- If applicable, add screenshots or a demo video -->

## Breaking Changes

<!-- If this PR introduces breaking changes, describe them here -->

- [ ] This PR introduces breaking changes
- [ ] Migration guide included
- [ ] Deprecation warnings added
- [ ] Documentation updated

**Breaking changes:**



## Checklist

<!-- Go over all the following points, and put an `x` in all the boxes that apply -->

### Code Quality

- [ ] My code follows the project's code style guidelines (PEP 8)
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have added docstrings to new functions/classes
- [ ] I have used type hints where appropriate
- [ ] My changes generate no new warnings or errors
- [ ] I have removed unnecessary debug prints/comments

### Documentation

- [ ] I have updated the documentation accordingly
- [ ] I have updated README.md (if needed)
- [ ] I have updated README.ru.md (if needed)
- [ ] I have added/updated code comments
- [ ] I have updated docstrings

### Testing

- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested with both Russian and Kyrgyz languages (if applicable)
- [ ] I have tested all three response modes: base, pro, search (if applicable)

### Dependencies

- [ ] I have checked that no new dependencies introduce security vulnerabilities
- [ ] I have updated `requirements.txt` (if needed)
- [ ] New dependencies are justified and documented

### Security

- [ ] My changes do not expose sensitive information
- [ ] I have not hardcoded any secrets, API keys, or passwords
- [ ] I have followed security best practices
- [ ] Input validation is properly implemented (if applicable)

## Performance Impact

<!-- Describe any performance implications -->

- [ ] No performance impact
- [ ] Performance improvement (describe below)
- [ ] Potential performance degradation (describe below and justify)

**Details:**



## Database Changes

<!-- If this PR affects the database schema or data -->

- [ ] No database changes
- [ ] Schema changes (describe below)
- [ ] Data migration required (provide script/instructions)
- [ ] Backwards compatible

**Details:**



## Deployment Notes

<!-- Special instructions for deployment -->

- [ ] No special deployment steps required
- [ ] Environment variables need to be updated
- [ ] Database migration needs to be run
- [ ] Dependencies need to be updated (`pip install -r requirements.txt`)
- [ ] Service restart required

**Instructions:**



## Additional Context

<!-- Add any other context about the PR here -->

## Reviewer Notes

<!-- Any specific areas you want reviewers to focus on -->

**Please review:**



---

<!-- 
For Reviewers:
- Verify code quality and adherence to project standards
- Check for potential security issues
- Verify documentation is updated
- Test the changes locally if possible
- Ensure CI/CD checks pass
-->
