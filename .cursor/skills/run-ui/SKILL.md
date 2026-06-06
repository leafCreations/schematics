---
name: run-ui
description: Launch the project UI with configurable structure and stage arguments.
---

When the user asks to open, launch, run, or start the UI, use the `run-ui` command.

Default command:

```bash
run-ui
```

Default values:

- structure: `residence`
- stage: `1`

If the user specifies a structure and/or stage, pass them as arguments:

```bash
run-ui <structure> <stage>
```

Examples:

```bash
run-ui
run-ui residence 2
run-ui blacksmith 1
run-ui farm 3
```

Argument rules:

- If only a structure is specified, use stage `1`.
- If no arguments are specified, use `residence` and stage `1`.
- Always use the exact structure name provided by the user.

After running the command:

1. Verify that the UI started successfully.
2. Report any startup errors.
3. If startup fails, provide a concise summary of the likely cause and recommended fix.