# Compiler development methodology

## Purpose and boundaries

Use this reusable guidance when developing or reviewing a compiler. It explains common methods and learning questions; it does not define any project's language. Always follow the target project's specification and local instructions for its rules, task order, approvals, tools, and testing. Examples using C are illustrative only.

No compiler-design textbooks were present in the inspected Pothos repository, so this version does not claim to summarize or cite the course's two textbooks. Add textbook references only after the actual editions and relevant material are available. The guidance below is general engineering methodology, not a fabricated textbook attribution.

## Establish the project model

Before designing a component, find the language specification, examples, current implementation, tests, build/run commands, and interfaces between stages. Record what is implemented and what is verified separately. Draw a small flow of actual data: source characters → tokens → syntax representation → semantic checks → only the outputs the project requires. Do not add stages merely because they are common.

For each language rule, locate its authoritative source, identify its implementation site, and create tests from the rule's examples and boundaries. If rules conflict, describe the alternatives and defer behavior changes to the project owner.

## Compiler component responsibilities

- **Lexical analysis** groups characters into tokens and reports malformed lexemes. It should not decide whether a token sequence forms a valid statement.
- **Syntax analysis** checks token order against a grammar and builds the representation the next required stage needs (parse tree or AST). It should not silently invent semantic constraints.
- **Semantic analysis** checks contextual rules the grammar cannot express, such as declared-name use or type compatibility, only when the language specifies them.
- **Intermediate representation** and **code generation** are optional stages. Add them only when the project requires them.

Keep interfaces explicit: input data, output data, errors, source locations, and failure behavior. Prefer simple records and focused functions over generic frameworks unless concrete requirements justify added machinery.

## Lexical analysis

### Regular definitions and token rules

Define character classes and regular definitions before writing the scanner. For example, an illustrative C-like identifier rule could be `letter (letter | digit)*`; this is not a rule for another language unless its specification says so. Keep the definitions distinct from code that advances input.

For each token, establish start characters, continuation characters, accepting condition, boundary/lookahead rule, and attributes. Decide from the target specification how to resolve overlapping tokens, often by the longest valid match and rule priority. Do not assume a language uses either policy without checking.

### Transition diagrams and scanner code

Represent states and transitions clearly. Each state should explain which input classes advance, which accept, and what happens on invalid input. When code uses numbered states from diagrams, preserve traceability with labels/comments and test transitions, including retraction/reprocessing of lookahead.

Track source position from the input cursor. Specify whether columns count bytes, Unicode code points, or another unit. Test start/end of file and newline conventions. Token attributes should preserve the lexeme and any required normalized value without losing source spelling when diagnostics or teaching output need it.

### Lexical errors

Choose error boundaries and recovery based on project requirements. A simple scanner may skip to a synchronization character and resume; recovery must always make progress to avoid loops. Preserve useful line/column and offending text. Test one error, multiple errors, unterminated constructs, invalid escapes, non-ASCII policy, and recovery after each error class.

## Grammars and parsing

Write down the approved context-free grammar before choosing a parser. Mark terminals, nonterminals, start symbol, epsilon productions, precedence, and associativity. Check examples against productions and identify ambiguity. Do not rewrite grammar solely to fit a preferred parser without approval when that changes the language.

Choose the simplest method allowed by the grammar and project deliverables:

- Recursive descent can make productions visible as functions and is straightforward for suitable grammars.
- Predictive LL parsing uses lookahead to choose productions. When required, FIRST sets describe terminals that can begin strings derived from a symbol; FOLLOW sets describe terminals that can follow a nonterminal; PREDICT sets help select productions. A parse table exposes conflicts and table-driven choices. Compute these from the actual grammar and verify nullable/epsilon cases.
- LR methods use parser states and lookahead-driven actions and may support a wider grammar class, with added tables/state machinery.

These are options, not mandatory deliverables. Explain any conflicts, grammar transformations and resulting language implications. Test every production, precedence/associativity cases, empty forms where allowed, malformed sequences, EOF, and expected recovery. Build only the parse structure needed by subsequent requirements.

## Semantic analysis and symbol information

Derive a checklist of semantic rules from the language definition. Typical categories can include declaration-before-use, duplicate declarations, type rules, function argument rules, and scope; they are examples, not automatic features.

If required, a symbol table maps names to attributes such as declared type or location. Nested scopes can be represented with a stack of tables or a parent-linked structure; choose the simplest design that matches specified lookup/shadowing behavior. Test scope entry/exit and each actual language rule. Keep diagnostics tied to the source span of the offending token or construct.

## Testing and integration

Test each phase independently using small inputs with known expected outputs, then test adjacent stage contracts, then the end-to-end path. For rule-based tests, cover ordinary examples, boundaries, invalid cases, and regression cases. Prefer tests derived from the specification over tests that merely repeat current implementation behavior.

When debugging, reduce a failing program to the smallest example that still fails. Inspect the token stream before debugging a parser; inspect the syntax representation before debugging semantic checks. Verify phase ordering, error propagation, source locations, and serialization at integration boundaries.

Do not describe a component as verified because it exists or because one sample works. Record actual commands, pass/fail counts, environment limitations, and known gaps.

## Student-facing explanation

For every implemented change, explain the actual code:

1. What compiler problem it solves and why the phase owns that problem.
2. The relevant functions and data structures.
3. How a small input moves through the algorithm.
4. How the behavior traces to the project's language source.
5. What tests exercise and what remains unverified.

Use diagrams or small traces when helpful. Label C or other language snippets as examples; never let them imply target-language syntax or semantics.
