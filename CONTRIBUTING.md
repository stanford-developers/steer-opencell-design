# Contributing to OpenCell Design

Thank you for your interest in contributing to OpenCell Design! This document provides guidelines and instructions for contributing.

## Contributor License Agreement (CLA)

**Before your first contribution can be merged, you must sign our [Contributor License Agreement](CLA.md).**

OpenCell Design is dual-licensed under AGPL-3.0 (open source) and a separate commercial license. The CLA grants the maintainers the right to distribute your contributions under both licenses. Without a signed CLA, we cannot accept your pull request.

When you open a pull request, a bot will comment with instructions to sign. Simply reply with the required statement and the check will pass automatically.

## Getting Started

1. **Fork** the repository and clone your fork:
   ```bash
   git clone https://github.com/stanford-developers/steer-opencell-design
   cd steer-opencell-design
   ```
2. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. **Install** in development mode:
   ```bash
   pip install -e .
   ```

## Making Changes

- Follow the existing code style and conventions.
- Keep changes focused — one feature or fix per pull request.

## Testing

- Write tests in the `test/` directory following the existing `test_<module>.py` naming convention.
- Run the full test suite before submitting:
  ```bash
  pytest
  ```
- Run a specific test with:
  ```bash
  pytest -k <test_name>
  ```

## Submitting a Pull Request

1. Push your branch to your fork.
2. Open a pull request against the `main` branch with a clear description of the change.
3. Ensure all tests pass.
4. Sign the CLA when prompted by the bot.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with a clear description and, if applicable, steps to reproduce the problem.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating.

## License

By contributing, you agree that your contributions will be licensed under the [AGPL-3.0](LICENSE) license and, per the CLA, may also be distributed under the project's commercial license.
