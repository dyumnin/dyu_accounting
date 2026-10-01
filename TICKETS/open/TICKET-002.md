# TICKET-002: Document config.json schema and options

**Status**: open
**Type**: improvement
**Priority**: medium
**Stage**: needs-spec
**Created**: 2026-09-29
**Parent**: none

## Problem / Motivation

`config.json` is loaded in `__init__.py` but no documentation exists describing what fields are required, what they mean, or what valid values are. Users must reverse-engineer by reading code or examining example. This is error-prone and frustrating.

## Acceptance Criteria

- [ ] Reference document (CONFIG.md) lists all required and optional config.json fields
- [ ] Each field has: name, type (string/number/boolean), required Y/N, default value (if any), description, and example values
- [ ] Document maps config fields to how they're used in code (which report, which feature)
- [ ] Provide a template `config.json` with all fields and inline comments
- [ ] Include a validation checker or schema file (JSON Schema or similar)

## Design Notes

Create `CONFIG.md` in root and provide a commented template config.json. Consider adding a `--validate-config` CLI option to help users catch config errors early.

## Files Affected

- `CONFIG.md` — new configuration reference
- `config.json.example` — template with all fields and comments
- `dyu_accounting/__init__.py` — optionally add config validation

## Implementation Notes

(To be filled during implementation)

## Testing

Verify every field in template and reference works with report generation.

