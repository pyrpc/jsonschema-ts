# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [SemVer](https://semver.org/).

## [Unreleased]

### Added

- `convert()` — convert single JSON Schema to TypeScript interface
- `convert_all()` — batch convert all `$defs` in a single npx call
- `collect_defs()` — extract and merge `$defs` from JSON Schema dicts
- `ensure_npx()` — check Node.js/npx availability
- `Options` dataclass — banner, formatting, unknownAny configuration
- `assemble()` — combine model interfaces and procedure types
- Error classes: `JsonschemaTsError`, `NodeRequiredError`, `ConversionError`
- Full test suite with 26+ unit tests and integration tests
- CI/CD workflows (GitHub Actions: test + publish to PyPI)
- Single-page documentation site
