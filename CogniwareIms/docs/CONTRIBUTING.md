# Contributing to Cogniware OPEA IMS

Thank you for your interest in contributing to the Cogniware OPEA Inventory Management System! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/opea-project/GenAIExamples/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs. actual behavior
   - Environment details (OS, Docker version, etc.)
   - Logs or screenshots if applicable

### Suggesting Enhancements

1. Check existing issues and discussions
2. Create an issue describing:
   - Feature description and use case
   - Benefits and potential impact
   - Possible implementation approach

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow coding standards (see below)
   - Add tests for new features
   - Update documentation

4. **Commit your changes**

   ```bash
   git commit -m "feat: Add amazing feature"
   ```

   Use conventional commits format:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `style:` Formatting
   - `refactor:` Code restructuring
   - `test:` Adding tests
   - `chore:` Maintenance

5. **Push to your fork**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Clear description of changes
   - Reference related issues
   - Include screenshots if UI changes

## Development Setup

### Prerequisites

- Docker 24.0+
- Docker Compose 2.0+
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- Git

### Local Development

**Backend:**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Run locally
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Type checking
npm run type-check
```

## Coding Standards

### Python (Backend)

- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for functions/classes

```python
def example_function(param: str) -> Dict[str, Any]:
    """
    Brief description of function.

    Args:
        param: Description of parameter

    Returns:
        Dictionary with results
    """
    return {"result": param}
```

**Formatting:**

```bash
# Format code
black backend/

# Lint
flake8 backend/

# Type check
mypy backend/
```

### TypeScript (Frontend)

- Follow TypeScript best practices
- Use functional components with hooks
- PropTypes or TypeScript interfaces
- Maximum line length: 100 characters

```typescript
interface ExampleProps {
  data: string;
  onUpdate: (value: string) => void;
}

export function ExampleComponent({ data, onUpdate }: ExampleProps) {
  // Component implementation
}
```

**Formatting:**

```bash
# Format code
npm run lint

# Type check
npm run type-check
```

### Docker

- Multi-stage builds
- Minimal base images (alpine, slim)
- Security best practices
- Clear documentation

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_services.py
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# With coverage
npm test -- --coverage
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Run integration tests
./scripts/test_e2e.sh
```

## Documentation

- Update README.md for feature changes
- Add inline comments for complex logic
- Update API documentation
- Include examples in docstrings

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Examples:**

```
feat(backend): Add knowledge base search endpoint

Implements semantic search functionality using OPEA retrieval service.

Closes #123
```

```
fix(frontend): Resolve login button not clickable

Updated z-index and pointer events to fix button interaction.

Fixes #456
```

## Pull Request Process

1. **Ensure all tests pass**
2. **Update documentation**
3. **Follow code review feedback**
4. **Squash commits** if requested
5. **Wait for approval** from maintainers

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No merge conflicts
- [ ] PR description is clear

## OPEA Integration Guidelines

When working with OPEA components:

1. **Follow OPEA API specifications**
   - Use standard endpoints
   - Respect rate limits
   - Handle errors gracefully

2. **Microservice Communication**
   - Use async/await for API calls
   - Implement retry logic
   - Add timeouts

3. **Model Configuration**
   - Document model requirements
   - Provide fallback options
   - Test with different models

## Release Process

Maintainers will handle releases:

1. Version bump (semantic versioning)
2. Update CHANGELOG.md
3. Create release tag
4. Build and publish Docker images
5. Update documentation

## Community

- **Discussions**: GitHub Discussions
- **Issues**: GitHub Issues
- **Email**: support@cogniware.com

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## Questions?

- Check existing documentation
- Search closed issues
- Ask in GitHub Discussions
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to Cogniware OPEA IMS! 🎉
