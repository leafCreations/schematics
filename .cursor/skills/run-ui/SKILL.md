---
name: run-ui
description: Launch the project UI with configurable structure and stage arguments.
---

When the user asks to open, launch, run, or start the UI, run from the **repo root**:

```bash
bash scripts/run-ui
```

Or with structure/stage:

```bash
bash scripts/run-ui <structure> <stage>
```

Default values:

- structure: `residence`
- stage: `1`

Examples:

```bash
bash scripts/run-ui
bash scripts/run-ui residence 2
bash scripts/run-ui blacksmith 1
bash scripts/run-ui farm 3
```

Argument rules:

- If only a structure is specified, use stage `1`.
- If no arguments are specified, use `residence` and stage `1`.
- Always use the exact structure name provided by the user.

The script uses `.venv/bin/python` when present, otherwise `python3`. It does **not** rely on a bare `python` command or a global `run-ui` on PATH.

Optional shell alias (add to `~/.zshrc` if you want the short command back):

```bash
alias run-ui='bash /path/to/structure_scripts/scripts/run-ui'
```

After running:

1. Verify that the UI started successfully.
2. Report any startup errors.
3. If startup fails, provide a concise summary of the likely cause and recommended fix.
