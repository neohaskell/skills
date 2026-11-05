# Choose response shape or enum evolution

Use only the branch needed by the task. Resolve the application revision and capabilities through [nh-app-context](../../nh-app-context/SKILL.md) before adapting API examples. The existing consumer layout and compatible API guide determine the actual imports, markers, and commands.

## Pattern — expose a status ADT as a stable text tag

When the public API specifies text tags, map the domain ADT explicitly as shown below. A schema-backed enum or tagged object may be equally appropriate. Adding a constructor changes the possible wire values even if the field is `Text`; coordinate schema and client compatibility through `nh-api-client`.

```haskell
-- Entity carries the ADT (in App.Context.Core):
--   data TaskStatus = Open | InProgress | Done

statusToText :: TaskStatus -> Text
statusToText status = case status of
  Open       -> "open"
  InProgress -> "in-progress"
  Done       -> "done"


instance QueryOf TaskEntity TaskSummary where
  queryId task = task.taskId

  combine task _maybeExisting =
    Update TaskSummary
      { taskSummaryId = task.taskId
      , status        = statusToText task.status   -- Text, not the ADT
      }
```

The read model field is `status :: Text`; the entity keeps the ADT. Illegal states stay unrepresentable in the domain while API consumers get the explicitly documented string enum (`"open"`/`"in-progress"`/…). See `neohaskell-domain-modeling` for the entity-side ADT.

---


## Query response shape

The HTTP endpoint returns results as a JSON object with an `items` array:

```json
{ "items": [ { "cartSummaryId": "...", "ownerId": "...", ... } ] }
```

When writing hurl assertions (see `write-hurl-e2e`), use `$.items[?...]` JSONPath, not `$[?...]`.

---

