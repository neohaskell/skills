# Repository instructions

## English-only persistence

Write all persisted content in English. This includes documentation, skills,
examples, code comments, human-readable script output, generated artifacts,
issue-tracker text, commit messages, pull requests, and release notes.

Use English filenames and directory names. Translate existing non-English prose
when working in this repository and update references when renaming its files.
Preserve the meaning, requirements, and decisions during translation.

Keep exact API identifiers, protocol fields, external URLs, proper names, and
required original license notices intact. They are identifiers or attribution,
not an alternative language for repository prose.

## Domain documentation

Use the root `GLOSSARY.md` and `docs/adr/` as the existing single-context layout.
Read relevant decisions before changing their subject. Keep temporary task
evidence outside reusable skill resources.

## Collection maintenance

Follow the agreed NH-152 scope: preserve the 27 historical skill names, adapt the
65 selected upstream skills with `nh-` names, and add the four application skills.
Keep resources inside their owning skill and use relative links between skills.
Git records content and history; do not add a separate catalog or provenance
manifest. Evaluation campaigns and acceptance certification are excluded from
this delivery.
