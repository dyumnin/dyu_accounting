# TICKET-001: Add step-by-step setup guide for new users

**Status**: open
**Type**: improvement
**Priority**: medium
**Stage**: needs-spec
**Created**: 2026-09-29
**Parent**: none

## Problem / Motivation

New users struggle to understand the initial setup process. The current README jumps to "install and run command" without explaining the prerequisites (chart of accounts, config.json structure, beancount file structure). A beginner needs a walkthrough from zero to first report generation.

## Acceptance Criteria

- [ ] Step-by-step guide document (SETUP.md) covers: prerequisites, folder structure, chart of accounts creation, config.json creation with explanations, initial transaction entry, and first report run
- [ ] Guide uses the example project as reference but walks through from scratch
- [ ] Code examples show before/after for each step
- [ ] Document includes common mistakes and troubleshooting
- [ ] Guide is accessible to someone with accounting knowledge but no beancount experience

## Design Notes

Create a new `SETUP.md` file in root directory that mirrors the annual user workflow but tailored for first-time setup. Should reference the existing example but not assume prior knowledge of beancount syntax.

## Files Affected

- `SETUP.md` — new comprehensive setup guide
- `README.md` — add link to SETUP.md in introduction

## Implementation Notes

(To be filled during implementation)

## Testing

Verify guide by following it step-by-step with fresh setup in test environment.

