---
name: nh-roles
description: Resolve roles, available tools, and model/effort settings for authorized application workflows without overriding the consumer or host configuration.
---

> Adapted for consumer applications from the public NeoHaskell project.

# Roles and host capabilities

This is the collection's single owner of role configuration. A role mapping does not authorize delegation. The user's instructions, consumer repository policy, host availability, and configured provider/model/effort take precedence.

| Role | Responsibility | Selection |
|---|---|---|
| Explorer | Read relevant source and return bounded evidence | Inherit the configured model unless the user or consumer explicitly maps this role. |
| Implementer | Own one bounded change and its delivery | Use the configured provider/model and supported effort. |
| Reviewer | Assess the current artifact independently when required | Use a separate authorized reader; self-review is not independence. |
| Coordinator | Maintain scope, ownership, dependencies, and completion evidence | Use the active host's actual coordination facilities. |
| Explainer | Synthesize cited behavior for the reader | Preserve the configured model and relevant source limits. |

1. Read the actual delegation interface and available capacity. Use only supported tool names, model identifiers, and separate effort controls.
2. Apply an explicit consumer role override only when supported and authorized. Never infer that a public model name is available in this account or switch providers implicitly.
3. If delegation is unavailable or forbidden, perform eligible work inline. If a required independent judgment or cross-model comparison cannot be supplied, report that precise limitation; do not label an author's check independent.
4. Keep one writer per owned checkout/artifact and use self-contained briefs. Preserve complete requested scope when scheduling work in batches.
5. Change role configuration only when requested. Keep application-specific mappings in separate consumer extensions, leaving managed collection content intact. Do not rewrite global provider settings.

Coordination lives in [nh-orchestrate](../nh-orchestrate/SKILL.md); application routing lives in [neohaskell-feature-pipeline](../neohaskell-feature-pipeline/SKILL.md).
