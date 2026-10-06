import { basicSetup, EditorView } from "codemirror";
import { Compartment } from "@codemirror/state";
import { HighlightStyle, StreamLanguage, syntaxHighlighting } from "@codemirror/language";
import { tags } from "@lezer/highlight";
import mireLanguage from "./language.json";
import darkLogo from "./logo_dark.png";
import lightLogo from "./logo_light.png";
import './style.css'
import './language.json'
import './logo_dark.png'
import './logo_light.png'

const htmlElement = document.documentElement;
const editorHost = document.getElementById("editor");
const themeBtn = document.getElementById("themeBtn");
const themeLogo = document.getElementById("themeLogo");
const runBtn = document.getElementById("rubBtn");
const lexerTableBody = document.querySelector("#lexerbox tbody");
const errorOutput = document.querySelector("#errorBox code");
const themeCompartment = new Compartment();
const sourceStorageKey = "pothos-lexer-source";
const syntax = mireLanguage.syntax;
const reservedWords = new Set(syntax.reservedWords);
const booleans = new Set(syntax.literals.booleans);
const nullLiterals = new Set(syntax.literals.null);
const symbolTokens = [...syntax.symbols, ...syntax.delimiters.separators]
    .sort((left, right) => right.length - left.length);
const delimiterTokens = syntax.delimiters.pairs
    .flatMap(({ open, close }) => [open, close])
    .sort((left, right) => right.length - left.length);
const mireTheme = mireLanguage.theme;

const mireLanguageSupport = StreamLanguage.define({
    name: mireLanguage.name.toLowerCase(),
    startState: () => ({ inBlockComment: false }),
    token(stream, state) {
        if (state.inBlockComment) {
            if (stream.match(syntax.comments.block.close)) state.inBlockComment = false;
            else stream.next();
            return "comment";
        }

        if (stream.eatSpace()) return null;
        if (stream.match(syntax.comments.block.open)) {
            state.inBlockComment = true;
            return "comment";
        }
        if (stream.match(syntax.comments.line)) {
            stream.skipToEnd();
            return "comment";
        }

        const quote = syntax.strings.quotes.find((mark) => stream.match(mark, false));
        if (quote) {
            stream.match(quote);
            while (!stream.eol()) {
                if (stream.match(syntax.strings.escape)) {
                    stream.next();
                    if (!stream.eol()) stream.next();
                } else if (stream.match(quote)) {
                    break;
                } else {
                    stream.next();
                }
            }
            return "string";
        }

        if (stream.match(/^(?:0[xX][\da-fA-F]+|0[bB][01]+|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)/)) return "number";
        if (stream.match(/^[\p{L}_][\p{L}\p{N}_]*/u, false)) {
            const word = stream.match(/^[\p{L}_][\p{L}\p{N}_]*/u)[0];
            if (booleans.has(word)) return "bool";
            if (nullLiterals.has(word)) return "null";
            return reservedWords.has(word) ? "keyword" : "variableName";
        }

        if (stream.match(delimiterTokens.find((token) => stream.match(token, false)) || /$^/)) return "bracket";
        if (stream.match(symbolTokens.find((token) => stream.match(token, false)) || /$^/)) return "operator";
        stream.next();
        return null;
    },
});

const mireHighlightStyle = HighlightStyle.define([
    { tag: tags.keyword, color: mireTheme.reservedWord, fontWeight: "bold" },
    { tag: tags.operator, color: mireTheme.symbol },
    { tag: tags.bracket, color: mireTheme.delimiter },
    { tag: tags.string, color: mireTheme.string },
    { tag: tags.number, color: mireTheme.number },
    { tag: tags.bool, color: mireTheme.reservedWord },
    { tag: tags.null, color: mireTheme.reservedWord },
    { tag: tags.comment, color: mireTheme.comment, fontStyle: "italic" },
]);

function readSavedSource() {
    try {
        return localStorage.getItem(sourceStorageKey) ?? "";
    } catch (error) {
        console.warn("Could not read saved source:", error);
        return "";
    }
}

function showErrors(errors) {
    if (!errorOutput) return;
    errorOutput.textContent = Array.isArray(errors) && errors.length
        ? errors.map(({ line, column, message }) => `Line ${line}, column ${column}: ${message}`).join("\n")
        : "No errors found.";
}

const editorTheme = (dark) => EditorView.theme({
    "&": {
        height: "100%",
        color: "var(--font-color)",
        backgroundColor: "var(--bg-lv-1)",
    },
    ".cm-content": {
        caretColor: "var(--font-color)",
    },
    ".cm-gutters": {
        color: "var(--font-color)",
        backgroundColor: "var(--bg-lv-1)",
        borderRight: "1px solid var(--card-border)",
    },
    ".cm-activeLine, .cm-activeLineGutter": {
        backgroundColor: "color-mix(in srgb, var(--font-color) 8%, transparent)",
    },
    "&.cm-focused .cm-cursor": {
        borderLeftColor: "var(--font-color)",
    },
    ".cm-selectionBackground, &.cm-focused .cm-selectionBackground": {
        backgroundColor: "color-mix(in srgb, var(--font-color) 24%, transparent)",
    },
}, { dark });

const editor = editorHost
    ? new EditorView({
        parent: editorHost,
        extensions: [
            basicSetup,
            mireLanguageSupport,
            syntaxHighlighting(mireHighlightStyle),
            themeCompartment.of(editorTheme(htmlElement.dataset.theme === "dark")),
            EditorView.updateListener.of((update) => {
                if (!update.docChanged) return;
                try {
                    localStorage.setItem(sourceStorageKey, update.state.doc.toString());
                } catch (error) {
                    console.warn("Could not save source:", error);
                }
            }),
        ],
        doc: readSavedSource(),
    })
    : null;

if (runBtn) {
    runBtn.addEventListener("click", async () => {
        if (!editor) return;

        runBtn.disabled = true;
        try {
            const response = await fetch("./api.json", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code: editor.state.doc.toString() }),
            });

            if (!response.ok) {
                throw new Error(`Request failed: ${response.status}`);
            }

            const result = await response.json();
            const tokens = Array.isArray(result) ? result : result.tokens;
            showErrors(result.errors);
            if (lexerTableBody && Array.isArray(tokens)) {
                lexerTableBody.replaceChildren();
                tokens.forEach(({ no, lexeme, token }) => {
                    const row = document.createElement("tr");
                    [no, lexeme, token].forEach((value) => {
                        const cell = document.createElement("td");
                        cell.textContent = String(value ?? "");
                        row.append(cell);
                    });
                    lexerTableBody.append(row);
                });
            }
        } catch (error) {
            console.error("Could not submit source code:", error);
            try {
                // Load the sample response on demand so the example error is visible.
                const sampleResponse = await fetch("./api.json");
                if (!sampleResponse.ok) throw new Error(`Request failed: ${sampleResponse.status}`);
                const sample = await sampleResponse.json();
                showErrors(sample.errors);
            } catch (sampleError) {
                showErrors([{ line: "—", column: "—", message: error.message || "Could not submit source code." }]);
            }
            if (lexerTableBody) {
                lexerTableBody.innerHTML = '<tr><td colspan="3">Could not submit source code</td></tr>';
            }
        } finally {
            runBtn.disabled = false;
        }
    });
}

if (themeBtn) {
    if (themeLogo) {
        themeLogo.src = htmlElement.dataset.theme === "dark" ? darkLogo : lightLogo;
    }
    themeBtn.addEventListener("click", () => {
        const next = htmlElement.dataset.theme === "light" ? "dark" : "light";
        htmlElement.dataset.theme = next;
        if (themeLogo) {
            themeLogo.src = next === "dark" ? darkLogo : lightLogo;
        }
        if (editor) {
            editor.dispatch({
                effects: themeCompartment.reconfigure(editorTheme(next === "dark")),
            });
        }
    });
}
