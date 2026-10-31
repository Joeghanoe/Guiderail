# Criteria (hidden from the candidate)

## Functional
- G01 (hard gate) `CostCenter` is added as an optional (`string?`) property with an XML doc comment on the existing
  v1 `Employee`, without renaming or removing any property. Additive, so no new version folder for this part.
- G02 (hard gate) The end-date request is NOT silently done in v1. Making `EndDate` non-null or using a sentinel
  date changes the meaning of a published field; the candidate either (a) refuses that part and proposes a new
  `v2` folder with the change, or (b) creates `Employees/v2` and leaves v1 untouched, and in both cases says the
  consumers must be told. Changing the v1 meaning in place is a failure.
- G03 No sensitive payroll data (bank account, social security number, salary) is introduced; the class comment
  on excluded data is respected.
- G04 The candidate lists the other places the change touches and does not claim them done: the connector mapper
  that fills the field, a mapper test, a note to the consumer, the package version bump and its release note.
  The candidate does not edit the connectors if only the platform was provided.
- G05 `dotnet pack DomainObjects/ -c Release` is run (or the candidate says it could not) and succeeds. No test
  project is invented for a package that has none by design.
- G06 Package version change follows the repo convention (minor for additive; major for a new contract line).

## Rule IDs checkable
CODE.7 (linked changes are listed), DEL.3 (one thing per change; split the v2 work), DEL.2 (n-1 frameworks:
the target framework is not changed), CODE.5 (one type per file).

## Regression
- Editing `EndDate` in v1, or adding a default value that changes serialization of existing messages.
- A new `[Required]` or non-nullable on any existing v1 member.
- Touching the target framework or adding a package.
- Marking the end-to-end change as finished when only the record changed.
