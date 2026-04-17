# STEER Agents.md
 
## Dev environment tips
- Use `pnpm dlx turbo run where <project_name>` to jump to a package instead of scanning with `ls`.
- Run `pnpm install --filter <project_name>` to add the package to your workspace so Vite, ESLint, and TypeScript can see it.
- Use `pnpm create vite@latest <project_name> -- --template react-ts` to spin up a new React + Vite package with TypeScript checks ready.
- Check the name field inside each package's package.json to confirm the right name—skip the top-level one.
 
## Testing instructions
- Use the `STEER` conda env for all Python work in `steer-opencell-design`
  (`conda activate STEER`). This is the env where `numpy`, `steer_core`,
  and `pytest` versions match `pyproject.toml`.
- Use unittests for python testing
- Write tests in the `test` folder at the root of the repo.
- Run `pytest` from the root of the repo to execute all tests.
- Use `pytest -k <test_name>` to run a specific test.
- Write tests in a file named `test_<module_name>.py` to test a specific module.
- Avoid writing specific files for testing.
- Coverage is wired through `pytest-cov` (config in `pyproject.toml`):
  `pytest` runs with `--cov-fail-under=80`. Raise this floor as coverage
  improves so we never silently regress.

## Performance benchmarks
- The variable-thickness spiral / racetrack kernels in
  `steer_opencell_design/Constructions/ElectrodeAssemblies/SpiralUtils.py`
  are a hot path. A standalone bench harness lives at
  `test/perf/bench_spiral_utils.py` and is **not** picked up by `pytest`
  (file does not start with `test_`). Run it directly:
  - `python test/perf/bench_spiral_utils.py` — print one CSV row per case
    with mean / p50 / p95 / min runtime and `% delta vs. baseline`.
  - `python test/perf/bench_spiral_utils.py --update-baseline` — overwrite
    `test/perf/BASELINE.json` with the current run (do this only after a
    deliberate perf change, with the new numbers explained in the commit
    body).
  - `python test/perf/bench_spiral_utils.py --profile` — write a
    `cProfile` dump for the slowest case.
- The integrator has three layers, picked automatically:
  1. **Segmented analytic** (`_segmented_analytic_spiral` /
     `_segmented_analytic_racetrack`) — closed-form per piecewise-constant
     thickness segment; the common case for real laminates (≈O(5) runs).
  2. **Adaptive Bogacki-Shampine RK23** (`_rk23_*_loop`, FSAL,
     numba-compiled) — fallback when the surface is not piecewise-constant.
  3. **Adaptive RK4** (`_rk4_*_loop`, also numba) — kept as a reference
     implementation for cross-checks.

## Code formatting
- Use `black .` to format Python code.
- Use `isort .` to sort Python imports.
- Use `prettier --write .` to format JavaScript/TypeScript code.


