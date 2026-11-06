# NeoHaskell Application Skills

Agent skills for building NeoHaskell applications—from business rules and APIs to frontend workflows and tests. For Claude Code and Codex.

Skills are reusable instructions that guide your coding agent through a task. This collection brings **97 skills** together: understand the application, model its behavior, implement the change, and check that it works across the affected components. It follows your project's existing frontend stack and includes its own examples and resources.

## Install

Run from your project directory with **Node.js 22.20 or newer**:

```sh
npx skills add neohaskell/skills --skill '*'
```

Choose your coding agent and project installation when prompted. The `--skill '*'` flag selects the complete collection so skills can use each other's guidance. Commit the installed files and lockfile with your project to share them with your team.

## Build your first feature

Open your coding agent in the project and describe what you want to build:

```text
Use neohaskell-feature-pipeline to add order cancellation.
Customers can cancel before shipment and see the updated status
in their order history.
```

The [feature pipeline](skills/neohaskell-feature-pipeline/SKILL.md) delivers full-stack features by default: inspect your application, clarify missing business rules, implement backend, API client, and frontend, and verify the real user journey. It automatically invokes [nh-frontend-setup](skills/nh-frontend-setup/SKILL.md) when the frontend or API-generation tooling is missing. A new frontend starts with React, TypeScript, and Orval; existing application choices are preserved.

Setup makes SDK generation from your configured service URL a prerequisite of each frontend build and the development command's initial compilation. The backend must be reachable: generation failure stops the command instead of reusing an old SDK. Installing this collection distributes the skills; the pipeline configures your application only when needed.

The workflow scales with the change. A button label uses frontend guidance; a new business workflow can involve event modeling, commands, projections, API clients, and UI. You can also name a specialist directly when you know what you need.

## Choose a starting point

| I want to… | Use this skill |
|---|---|
| Build a feature or fix a bug across the app | [neohaskell-feature-pipeline](skills/neohaskell-feature-pipeline/SKILL.md) |
| Understand an existing app before changing it | [nh-app-context](skills/nh-app-context/SKILL.md) |
| Connect a frontend client to the backend API | [nh-api-client](skills/nh-api-client/SKILL.md) |
| Build or improve an interface in the existing stack | [nh-frontend](skills/nh-frontend/SKILL.md) |
| Review NeoHaskell code and affected clients | [neohaskell-code-review](skills/neohaskell-code-review/SKILL.md) |

[Browse all skills](skills/). Detailed guidance is loaded as needed for the task.

## Updates

Ask your agent to use [nh-skills](skills/nh-skills/SKILL.md) to update or recover an installation. It guides comparison of existing files, preservation of customizations, and review of the update as a separate Git change. Keep project-specific instructions in separate skills so collection updates can preserve them.

## Credits and license

The design methodology adapts Event Modeling and outside-in TDD material from [jwilger/claude-code-plugins](https://github.com/jwilger/claude-code-plugins). Shared procedures are adapted from [NeoHaskell](https://github.com/neohaskell/NeoHaskell).

See [LICENSE](LICENSE) and the applicable notices included with individual skills. For repository conventions and design decisions, see [AGENTS.md](AGENTS.md), [GLOSSARY.md](GLOSSARY.md), and [the ADRs](docs/adr/).
