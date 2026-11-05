> Adapted for consumer applications from the public NeoHaskell project.

# Consumer static checks

Use the consumer's maintained lint command and configuration. Discover its HLint version, source scope, enabled extensions, warnings policy, and any intentional ownership exceptions. This collection does not install a `.hlint.yaml` or a CI gate.

The optional `scripts/check.py` reads the current component (or `NH_APP_ROOT`), tracked and unignored source, and local HLint configuration. Pass `--hlint` for the executable and `--expected-version` only for the version the consumer pins. `--dialect-rules` additionally checks direct Text-parameter conventions; do not enable it for unrelated components. Exit 0 means no findings in the selected coverage, 1 means findings, and 2 means the check could not run.

The helper rejects literal runtime dependencies on `.agents-state`. It skips `.agents`, `.claude`, and `.github`. Source suffixes are listed in the script; generated files, dynamic paths, Haskell types, and concurrency semantics require separate reasoning. Findings must be interpreted against the consumer's policy. Included fixtures are illustrative parser inputs, not a certification of this consumer.

## Language settings and evaluation timing

[cabal_extensions.py](../scripts/cabal_extensions.py) reads ordinary Cabal files, unconditional common stanza imports, component source directories, language, extensions, and `-X` options. It does not import framework starter templates. Conditional configuration, conflicting profiles, or unsupported syntax produce setup errors; use the application's established runner for these cases.

Temporary parser inputs normalize `Strict` and `NoStrict` and retain source locations. This mechanism originated with HLint 3.10; confirm compatibility with the consumer's version before relying on it. A diagnostic mapping limitation is a tooling problem, not permission to change runtime evaluation. Source files remain unchanged.

Read [language extensions](../../nh-language-extensions/SKILL.md) before changing lazy patterns or defaults. Keep a required `~value` when construction must precede evaluation. For example, under `Strict`, `defer ~value = Deferred (\_ -> value)` can construct a wrapper without demanding the wrapped value. Test construction and demanded execution separately for a real timing change.

## Coverage boundaries

[source_rules.py](../scripts/source_rules.py) supports layout-based modules and a finite set of known constructor imports, signature shapes, and formatting expressions. It does not infer types, expand aliases, or establish runtime semantics. Any framework-specific conversion exceptions in that scanner are inert unless the optional dialect rule is selected and the exact source identity matches. Never copy framework owner exceptions into application policy without a concrete reason.

For design questions, consult [reader-oriented names](../../nh-principle-name-for-the-reader/SKILL.md) and [service design](../../nh-best-practices/references/readable-services.md). Do not equate a clean static check with delivery of an application feature.
