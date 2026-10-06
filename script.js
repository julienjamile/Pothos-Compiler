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
const runBtn = document.getElementById("runBtn");          // renamed from rubBtn
const skipCommentsChk = document.getElementById("skipCommentsChk");
const traceChk = document.getElementById("traceChk");
const lexerTableBody = document.querySelector("#lexerbox tbody");
const lexerTableHead = document.querySelector("#lexerbox thead tr");
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

/**
 * showErrors – render the errors array into #errorBox.
 *
 * Each error dict has { phase, line, column, message, text }.
 * Format: "Lexical Error [line L, col C]: message"  (matches the CLI format).
 */
function showErrors(errors) {
    if (!errorOutput) return;
    if (Array.isArray(errors) && errors.length) {
        errorOutput.textContent = errors
            .map(({ phase, line, column, message }) => {
                const phaseLabel = phase
                    ? phase.charAt(0).toUpperCase() + phase.slice(1) + " Error"
                    : "Error";
                return `${phaseLabel} [line ${line}, col ${column}]: ${message}`;
            })
            .join("\n");
    } else {
        errorOutput.textContent = "No errors found.";
    }
}

/**
 * showNetworkError – show a raw fetch/network error without falling back to
 * the fake sample data.
 */
function showNetworkError(error) {
    if (!errorOutput) return;
    errorOutput.textContent = `Request failed: ${error.message || String(error)}`;
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

/** Rebuild the table header to show/hide the optional Path column. */
function setTableColumns(showPath) {
    if (!lexerTableHead) return;
    const base = ["No.", "Lexeme", "Token", "Line", "Col"];
    if (showPath) base.push("Path");
    lexerTableHead.innerHTML = base.map((h) => `<th>${h}</th>`).join("");
}

if (runBtn) {
    runBtn.addEventListener("click", async () => {
        if (!editor) return;

        const skipComments = skipCommentsChk ? skipCommentsChk.checked : false;
        const trace = traceChk ? traceChk.checked : false;

        runBtn.disabled = true;
        try {
            const response = await fetch("./api.json", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    code: editor.state.doc.toString(),
                    skipComments,
                    trace,
                }),
            });

            const result = await response.json();

            if (!response.ok) {
                // HTTP 400 / 413 – the backend returned {"error": "..."}
                const msg = result.error || `HTTP ${response.status}`;
                showNetworkError(new Error(msg));
                if (lexerTableBody) {
                    const colSpan = trace ? 6 : 5;
                    lexerTableBody.innerHTML = `<tr><td colspan="${colSpan}">Request error</td></tr>`;
                }
                return;
            }

            const tokens = Array.isArray(result) ? result : result.tokens;
            showErrors(result.errors);
            setTableColumns(trace);

            if (lexerTableBody && Array.isArray(tokens)) {
                lexerTableBody.replaceChildren();
                if (tokens.length === 0) {
                    const colSpan = trace ? 6 : 5;
                    lexerTableBody.innerHTML = `<tr><td colspan="${colSpan}">No tokens</td></tr>`;
                } else {
                    tokens.forEach(({ no, lexeme, token, line, column, path }) => {
                        const row = document.createElement("tr");
                        const cells = [no, lexeme, token, line, column];
                        if (trace) cells.push(path ?? "");
                        cells.forEach((value) => {
                            const cell = document.createElement("td");
                            cell.textContent = String(value ?? "");
                            row.append(cell);
                        });
                        lexerTableBody.append(row);
                    });
                }
            }
        } catch (error) {
            // Network / parse failure – show the real error, no fake fallback.
            console.error("Could not submit source code:", error);
            showNetworkError(error);
            if (lexerTableBody) {
                const colSpan = trace ? 6 : 5;
                lexerTableBody.innerHTML = `<tr><td colspan="${colSpan}">Could not submit source code</td></tr>`;
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
