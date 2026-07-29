# Engineering Philosophy

## Stay skeptical, don't rush to features

When a solution seems obvious, resist implementing it immediately. First identify
the actual information or abstraction that's missing.

A request for "one more field" or "one more reference" can signal that the
wrong object is being asked to own information.

### Example from this codebase

While designing the runtime API, it initially seemed that `MapObject` should
carry layer information so users could access rendering metadata (z-index,
properties, etc.).

After examining the real workflow, the problem turned out to be much smaller.

The actual requirement was:

- Access object layer metadata.
- Discover which tilesets a layer references.
- Avoid exposing parser internals.

Adding parser references to every `MapObject` would have coupled a lightweight
collision/render helper to the parser model.

A smaller parser-level improvement was sufficient:

```python
ParsedLayer.ttypes: set[int]
```

This preserves ownership:

- Layers know which tilesets they reference.
- Objects know which tileset they use.
- `MapObject` remains focused on runtime collision/render concerns.

The runtime API stayed unchanged while advanced users gained the information
they needed through existing public parser APIs.

## Principles

- Identify the missing information before designing a solution.
- Put information where it naturally belongs. Ownership should reflect the domain model, not convenience.
- Prefer improving existing abstractions over introducing new ones.
- Prefer small parser metadata over larger runtime abstractions when possible.
- Avoid turning convenience classes into "objects that know everything."
- Test new behavior at the lowest practical layer.
- Don't introduce runtime coupling when a parser-level improvement is sufficient.

---

## Respect architecture, but don't hunt dragons

If an architectural limitation blocks real work, address it.

If it merely feels incomplete, wait until multiple real use cases point to the
same missing abstraction.

Avoid refactoring for hypothetical future flexibility.

Before changing the architecture, ask:

- What concrete problem am I solving?
- Who should own this information?
- Can a minimal change solve it?
- Does this reduce complexity or merely move it?

Prefer the smallest change that removes today's friction without constraining
tomorrow's design.

---

## Prefer composition over expansion

When an existing type starts accumulating unrelated responsibilities, consider
whether the functionality belongs in a helper, parser metadata, or another
existing abstraction instead.

A convenience type should remain convenient.

Advanced workflows should be enabled through composition of existing APIs rather
than expanding one class until it becomes responsible for everything.

---

## Validate assumptions

Treat suggestions—including your own—as hypotheses, not conclusions.

Before introducing a new abstraction or expanding an existing one:

1. Verify the actual pain point.
2. Trace where the missing information originates.
3. Ask whether ownership is already implied elsewhere.
4. Choose the smallest change that solves the real problem.
5. Validate the design with tests before committing.

The goal is not to minimize code changes at all costs, but to maximize clarity,
maintainability, and correct ownership while avoiding unnecessary complexity.

### Push back a little

Don't become a yes-machine.

If a suggestion looks questionable, argue your case. Explain why, offer an
alternative, and challenge assumptions.

If the user still insists after understanding the trade-offs, implement it.

Sometimes the best engineering decision is losing the argument gracefully.

If I ignore the explanation, acknowledge that the decision is technically
questionable, then implement it.

> "Wisdom was chasing you, but you were faster."
