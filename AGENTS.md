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
- Jelly rolls are wound by one numba kernel, `_wind_taut` in
  `steer_opencell_design/Constructions/ElectrodeAssemblies/Winding.py`, for
  round and flat (racetrack) mandrels alike. It winds the laminate's exact stack
  profile (`Laminate.get_stack_profile()`) turn on turn onto a template of P
  samples per turn, so each turn sits on the one beneath it, spanning taut (a
  local convex hull) over steps; `_drape_window` drapes the layers inside the
  stack the same way around each profile edge. See that module's docstring for
  the model. `SpiralCalculator.calculate_variable_thickness_spiral`
  / `_racetrack` are thin wrappers over it.
- Rolls are measured on the winding's outer envelope (the last turn's outer
  face). The full rebuild and the dimension setters' Brent objective read the
  same measurement, so they agree exactly; the objective winds and measures
  only (no layer paths, extrusion or placement).
- `test/perf/bench_spiral_utils.py` times the kernel through the wrappers, at
  default and high resolution. It is **not** picked up by `pytest` (the file
  does not start with `test_`). Run it directly:
  - `python test/perf/bench_spiral_utils.py` prints one CSV row per case with
    mean / p50 / p95 / min runtime and `% delta vs. baseline`.
  - `python test/perf/bench_spiral_utils.py --update-baseline` overwrites
    `test/perf/BASELINE.json` with the current run. Do this only after a
    deliberate perf change, with the new numbers explained in the commit body.
  - `python test/perf/bench_spiral_utils.py --profile` writes a `cProfile`
    dump for the slowest case.
- `test/perf/bench_jellyroll_setters.py` times the Brent-driven dimension
  setters: `WoundJellyRoll.radius`, `FlatWoundJellyRoll.thickness` and
  `FlatWoundJellyRoll.width`. Same CLI as the spiral bench; the baseline lives
  at `test/perf/BASELINE_SETTERS.json`, and `--profile` prints a per-stage
  table (stack profile, winding, measurement, layer paths, placement, tail).

## Code formatting
- Use `black .` to format Python code.
- Use `isort .` to sort Python imports.
- Use `prettier --write .` to format JavaScript/TypeScript code.


