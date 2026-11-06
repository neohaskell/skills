# Make first installation a single command

The default first installation is `npx skills add neohaskell/skills --skill '*'`, run in the consumer project. The user selects their coding agent and project scope through the installer. The command uses the repository's default branch and the current installer; resolving a release SHA and pinning the installer are optional rather than prerequisites for getting started.

Nick requested this simpler installation experience during the README review and approved the rewrite. This supersedes the mandatory pinned first-install procedure and dual-agent requirement in [ADR 0001](0001-collection-distribution.md). Complete collection installation remains required because skills reference one another. Consumers commit the installed content, lockfile, and any agent links together; Git preserves the installed state even when the source branch later moves.

The README leads with application outcomes, installation, and a first task. Release mechanics and recovery belong to `nh-skills`. Existing immutable releases and the pinned dual-agent procedure remain available for projects that explicitly choose them. The comparison helper supports that specific layout and metadata; a quick-start installation does not need to adopt them to be valid.

Updates still preserve customized and unrelated files, establish ownership before removals, and form a separate reviewable Git change. For quick-start installations, maintenance compares against the original installation recorded in Git or an identified upstream commit, preserving the user's agent selection. Missing baseline evidence requires resolving the uncertainty before replacement. Simplifying first installation does not authorize overwriting existing content or silent updates.
