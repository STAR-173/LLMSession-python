# Contributing to LLMSession

Thank you for your interest in contributing to **LLMSession**! We welcome all contributions including bug fixes, new features, documentation improvements, and more.

## Project Structure

*   **`src/`**: Contains the Python source code
*   **`verify_flow.py`**: Verification script for testing
*   **`verify_aistudio.py`**: Additional verification script
*   **`.github/workflows/`**: CI/CD workflows for automated publishing
*   **`pyproject.toml`**: Package configuration and dependencies

## Development Setup

### 1. Fork and Clone

1.  Fork the repository on GitHub
2.  Clone your fork locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/llm_session.git
    cd llm_session
    ```

### 2. Set Up Development Environment

1.  Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or
    .\venv\Scripts\activate   # Windows
    ```

2.  Install the package in **Editable Mode**:
    ```bash
    pip install -e .
    ```
    *This allows you to modify code in `src/` and test it immediately without reinstalling.*

3.  Install build tools (optional, for testing builds):
    ```bash
    pip install build
    ```

### 3. Testing Your Changes

We use manual verification scripts to test the full flow (Browser launch → Auth → Prompt).

```bash
python verify_flow.py
```

*Tip: You can modify `verify_flow.py` to use `headless=False` to watch the bot work in real-time.*

### 4. Building Locally

To test the build process locally before pushing:

```bash
python -m build
```

This will create distribution files in the `dist/` directory.

## Safety Warning (Credentials)

To test changes, you will likely need to put real credentials into `verify_flow.py`.

> [!CAUTION]
> **NEVER commit files containing your real passwords.**
> If you modify the verification scripts with real credentials, please revert those changes before pushing, or ensure they are ignored by git.

## Pull Request Process

1.  **Fork & Clone**: Fork the repo and clone it locally (see above)
2.  **Branch**: Create a feature branch from `main`:
    ```bash
    git checkout -b feature/your-feature-name
    ```
3.  **Code**: Implement your changes
    *   Adhere to **PEP 8** style guidelines
    *   Add docstrings to new functions and classes
    *   Keep code clean and well-commented
4.  **Test**: Run the verification scripts to ensure everything works:
    ```bash
    python verify_flow.py
    ```
5.  **Commit**: Use clear, descriptive commit messages:
    ```bash
    git commit -m "Add feature: description of what you added"
    ```
6.  **Push**: Push to your fork:
    ```bash
    git push origin feature/your-feature-name
    ```
7.  **Open PR**: Open a Pull Request against the `main` branch on GitHub

## Code Style Guidelines

*   Follow **PEP 8** conventions for Python code
*   Use meaningful variable and function names
*   Add comments for complex logic
*   Keep functions focused and single-purpose
*   Add type hints where appropriate

## Types of Contributions

### Bug Fixes

If you're fixing a bug:
1.  Describe the bug in your PR
2.  Explain how your fix resolves it
3.  Test thoroughly before submitting

### New Features

If you're adding a new feature:
1.  Open an issue first to discuss the feature
2.  Wait for maintainer feedback before implementing
3.  Update documentation (README.md) if needed
4.  Add examples showing how to use the feature

### Documentation

Documentation improvements are always welcome:
*   Fix typos or unclear explanations
*   Add more examples
*   Improve API documentation
*   Update outdated information

### Updating Selectors

If you're fixing broken selectors because ChatGPT updated their UI:
1.  Update `src/llm_session/providers/chatgpt.py`
2.  Test thoroughly with the verification script
3.  Document which elements changed in your PR description

## Automated Publishing (For Maintainers)

This project uses **GitHub Actions** for automated publishing to PyPI:

*   **Push to `main`**: Automatically publishes to TestPyPI for testing
*   **Push a version tag** (e.g., `v0.1.4`): Automatically publishes to PyPI

### Creating a Release (Maintainers Only)

1.  Update version in `pyproject.toml`:
    ```toml
    version = "0.1.4"
    ```

2.  Commit and push:
    ```bash
    git add pyproject.toml
    git commit -m "Release version 0.1.4"
    git push origin main
    ```

3.  Create and push a tag:
    ```bash
    git tag v0.1.4
    git push origin v0.1.4
    ```

4.  The GitHub Actions workflow will automatically build and publish to PyPI

## Getting Help

If you need help with contributing:
*   Open a [GitHub Discussion](https://github.com/star-173/llm_session/discussions)
*   Check existing [Issues](https://github.com/star-173/llm_session/issues)
*   Reach out to maintainers in your PR

## Code of Conduct

*   Be respectful and constructive
*   Welcome newcomers and help them learn
*   Focus on what is best for the community
*   Show empathy towards other community members

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to LLMSession! 🎉