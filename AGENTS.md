# STEER Agents.md
 
## Dev environment tips
- Use `pnpm dlx turbo run where <project_name>` to jump to a package instead of scanning with `ls`.
- Run `pnpm install --filter <project_name>` to add the package to your workspace so Vite, ESLint, and TypeScript can see it.
- Use `pnpm create vite@latest <project_name> -- --template react-ts` to spin up a new React + Vite package with TypeScript checks ready.
- Check the name field inside each package's package.json to confirm the right name—skip the top-level one.
 
## Testing instructions
- Use unittests for python testing
- Write tests in the `test` folder at the root of the repo.
- Run `pytest` from the root of the repo to execute all tests.
- Use `pytest -k <test_name>` to run a specific test.
- Write tests in a file named `test_<module_name>.py` to test a specific module.
- Avoid writing specific files for testing.  

## Code formatting
- Use `black .` to format Python code.
- Use `isort .` to sort Python imports.
- Use `prettier --write .` to format JavaScript/TypeScript code.


