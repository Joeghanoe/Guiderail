# Criteria (hidden from the candidate)

## Functional
- G01 (hard gate) The dead-letter call no longer receives the message body in its properties, in the reason, or in
  the description, on every path (unparseable, unsupported type, unsupported version, handler failure, last attempt).
- G02 (hard gate) No exception text or stack trace reaches the dead-letter reason, description or properties.
  The reason is a stable code or short fixed phrase plus the event type; the description may carry the delivery count.
- G03 The per-message custom event carries a reason code, not `exception.Message` / handler-supplied free text.
  `EventType`, `MessageVersion`, `MessageResult`, `CorrelationId` keep their names and values.
- G04 The exception is still available to operators: tracked once as an exception (not also logged in a second
  place with the same text), with the message id as the way to find it.
- G05 Handler-supplied `Failed(string)` text does not leak into queue or event output. Either the API gains a
  reason code overload and the old one maps to a generic code, or the text is kept out by the processor. The
  existing public signatures still compile for connectors (state the choice).
- G06 Tests: existing assertions that pin the old behaviour (description equals handler text; description contains
  the exception text; ErrorMessage contains text) are changed on purpose and the change is explained.
- G07 A new test pushes a sentinel string through the body, the handler failure text and the exception and asserts
  it appears in no dead-letter field, no custom event property and no log output captured by the fake logger.
- G08 `dotnet build -warnaserror` and `dotnet test` for the Foundation pass, or the candidate says it could not run them.

## Rule IDs checkable
SEC.2, OBS.3, CODE.2, CODE.4 (reason codes and property names are constants), T.1, T.4 (a test for the escaped defect).

## Regression
- Dead-lettering stops happening, or Succeeded/Skipped stop completing the message.
- Property names the alert query reads (`MessageResult`, `EventType`, `CorrelationId`) change.
- The rethrow option or the last-attempt behaviour changes.
- A catch that swallows the exception and returns success.
