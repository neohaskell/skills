---
name: nh-how
description: Explain how a consumer application works and locate the owner of a behavior before changing it, using current source and revision-compatible API guidance.
---

> Adapted for consumer applications from the public NeoHaskell project.

# Explain the application

Use [nh-app-context](../nh-app-context/SKILL.md) to locate the affected component, its effective framework revision, and compatible guide. Trace only mechanisms relevant to the question; local framework source paths are not assumed.

1. State the question's scope and inspect the real entrypoint, callers, data boundary, and implementation.
2. For a narrow question, explore inline. For complex independent angles, use [nh-roles](../nh-roles/SKILL.md) only when delegation is authorized and available. Explorers remain read-only.
3. Build a source-backed explanation of ownership, runtime flow, and relevant constraints. Read every source location before citing it. Use [nh-why](../nh-why/SKILL.md) when historical motivation matters.
4. Present Overview, Key Concepts, How It Works, Where Things Live, and Gotchas only where useful. Distinguish observed code from inference and unavailable dependencies.

For repeated navigation, [codemap](references/codemap.md) provides an optional worktree-local index of actual consumer source. It does not replace source inspection or create a permanent application inventory. For a live fault use [runtime forensics](references/playbooks/runtime-forensics.md); for an existing trace use [trace forensics](references/playbooks/trace-forensics.md).
