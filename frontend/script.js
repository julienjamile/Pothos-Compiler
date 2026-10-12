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
const autoRunChk = document.getElementById("autoRunChk");
const lexerBox = document.getElementById("lexerbox");
const errorBox = document.getElementById("errorBox");
const lexerTableBody = document.querySelector("#lexerbox tbody");
const lexerTableHead = document.querySelector("#lexerbox thead tr");
const errorTableBody = document.querySelector("#errorBox tbody");
const resultTabs = [...document.querySelectorAll("[data-result-tab]")];
const themeCompartment = new Compartment();
const sourceStorageKey = "pothos-lexer-source";
const outputStorageKey = "pothos-lexer-output";
let tokenRanges = [];
let activeTokenRows = new Set();
let activeErrorRow = null;
let autoRunTimer = null;
let autoRunPending = false;

function scheduleAutoRun() {
    if (!autoRunChk?.checked || !runBtn) return;
    window.clearTimeout(autoRunTimer);
    autoRunTimer = window.setTimeout(() => {
        autoRunTimer = null;
        if (!autoRunChk.checked) return;
        if (runBtn.disabled) {
            autoRunPending = true;
            return;
        }
        autoRunPending = false;
        runBtn.click();
    }, 300);
}

function setActiveResultTab(panel) {
    const showLexer = panel === "lexer";
    lexerBox?.classList.toggle("mobile-active", showLexer);
    errorBox?.classList.toggle("mobile-active", !showLexer);
    resultTabs.forEach((tab) => {
        const selected = tab.dataset.resultTab === panel;
        tab.setAttribute("aria-selected", String(selected));
        tab.tabIndex = selected ? 0 : -1;
    });
}

resultTabs.forEach((tab, index) => {
    tab.addEventListener("click", () => setActiveResultTab(tab.dataset.resultTab));
    tab.addEventListener("keydown", (event) => {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();
        const nextIndex = (index + (event.key === "ArrowRight" ? 1 : resultTabs.length - 1)) % resultTabs.length;
        const nextTab = resultTabs[nextIndex];
        setActiveResultTab(nextTab.dataset.resultTab);
        nextTab.focus();
    });
});

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
function getSourcePosition(lineStarts, sourceLines, line, column) {
    const lineIndex = Number(line) - 1;
    if (!Number.isInteger(lineIndex) || lineIndex < 0 || lineIndex >= sourceLines.length) return null;

    const columnIndex = Number(column) - 1;
    if (!Number.isInteger(columnIndex) || columnIndex < 0) return null;

    const characters = Array.from(sourceLines[lineIndex]);
    const start = lineStarts[lineIndex] + characters.slice(0, columnIndex).join("").length;
    return { start, characterLength: characters[columnIndex]?.length ?? 0 };
}

function showErrors(errors, lineStarts, sourceLines) {
    if (!errorTableBody) return;
    errorTableBody.replaceChildren();
    activeErrorRow = null;

    if (!Array.isArray(errors) || errors.length === 0) {
        const row = document.createElement("tr");
        row.innerHTML = '<td colspan="3">No errors found.</td>';
        errorTableBody.append(row);
        return;
    }

    errors.forEach(({ phase, line, column, message }) => {
        const row = document.createElement("tr");
        const position = getSourcePosition(lineStarts, sourceLines, line, column);
        if (position) {
            row.dataset.start = String(position.start);
            row.dataset.end = String(position.start + position.characterLength);
            row.tabIndex = 0;
        }

        [line, column].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = String(value ?? "");
            row.append(cell);
        });

        const messageCell = document.createElement("td");
        const phaseLabel = phase
            ? phase.charAt(0).toUpperCase() + phase.slice(1) + " Error"
            : "Error";
        messageCell.textContent = `${phaseLabel}: ${message ?? ""}`;
        row.append(messageCell);
        errorTableBody.append(row);
    });
}

/**
 * showNetworkError – show a raw fetch/network error without falling back to
 * the fake sample data.
 */
function showNetworkError(error) {
    if (!errorTableBody) return;
    errorTableBody.replaceChildren();
    activeErrorRow = null;
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 3;
    cell.textContent = `Request failed: ${error.message || String(error)}`;
    row.append(cell);
    errorTableBody.append(row);
}

function getTokenRange(lineStarts, sourceLines, line, column, lexeme) {
    const position = getSourcePosition(lineStarts, sourceLines, line, column);
    if (!position) return null;
    const start = position.start;
    const end = start + Array.from(String(lexeme)).join("").length;
    return { start, end };
}

function setActiveTokenRows(rows, scrollRow = null, behavior = "smooth", verticalRatio = null) {
    const nextRows = new Set(rows.filter(Boolean));
    const wasActive = scrollRow && activeTokenRows.has(scrollRow);
    activeTokenRows.forEach((row) => {
        if (!nextRows.has(row)) row.classList.remove("is-active");
    });
    nextRows.forEach((row) => {
        if (!activeTokenRows.has(row)) row.classList.add("is-active");
    });
    activeTokenRows = nextRows;
    if (scrollRow && nextRows.has(scrollRow)) {
        if (lexerBox && verticalRatio !== null) {
            const boxRect = lexerBox.getBoundingClientRect();
            const rowRect = scrollRow.getBoundingClientRect();
            const headerHeight = lexerBox.querySelector("thead")?.getBoundingClientRect().height ?? 0;
            const visibleTop = boxRect.top + lexerBox.clientTop + headerHeight;
            const visibleBottom = boxRect.top + lexerBox.clientTop + lexerBox.clientHeight;
            const rowIsVisible = rowRect.top >= visibleTop && rowRect.bottom <= visibleBottom;
            if (wasActive && rowIsVisible) return;

            const visibleHeight = lexerBox.clientHeight - headerHeight;
            const targetOffset = lexerBox.clientTop + headerHeight + visibleHeight * verticalRatio
                - rowRect.height / 2;
            const rowOffset = rowRect.top - boxRect.top + lexerBox.scrollTop;
            const maxScroll = lexerBox.scrollHeight - lexerBox.clientHeight;
            const targetScroll = Math.max(0, Math.min(maxScroll, rowOffset - targetOffset));
            lexerBox.scrollTo({ top: targetScroll, behavior });
        } else {
            scrollRow.scrollIntoView({ block: "nearest", behavior });
        }
    }
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
            EditorView.domEventHandlers({
                mousemove(event, view) {
                    if (view.state.selection.ranges.some(({ empty }) => !empty)) return false;

                    const position = view.posAtCoords({ x: event.clientX, y: event.clientY });
                    if (position === null) return false;

                    const range = tokenRanges.find(({ start, end }) => position >= start && position < end)
                        ?? tokenRanges.find(({ start, end }) => position === end && end > start);
                    setActiveTokenRows(range ? [range.row] : [], range?.row ?? null, "smooth", 2 / 3);
                    return false;
                },
                mouseleave(_event, view) {
                    if (view.state.selection.ranges.some(({ empty }) => !empty)) return false;
                    setActiveTokenRows([]);
                    return false;
                },
            }),
            EditorView.updateListener.of((update) => {
                if (update.selectionSet || update.docChanged) {
                    const selections = update.state.selection.ranges.filter(({ empty }) => !empty);
                    if (selections.length) {
                        const selectedRanges = tokenRanges.filter(({ start, end }) =>
                            selections.some((selection) => start < selection.to && end > selection.from));
                        const mainSelection = update.state.selection.main;
                        const primaryRange = selectedRanges.find(({ start, end }) =>
                            mainSelection.head >= start && mainSelection.head < end)
                            ?? selectedRanges.find(({ end }) => mainSelection.head === end);
                        const rows = selectedRanges.map(({ row }) => row);
                        setActiveTokenRows(rows, primaryRange?.row ?? rows.at(-1));
                    } else {
                        const cursor = update.state.selection.main.head;
                        const cursorLine = update.state.doc.lineAt(cursor).number;
                        const lineRanges = tokenRanges.filter(({ row }) => Number(row.dataset.line) === cursorLine);
                        const activeRange = lineRanges.find(({ start, end }) => cursor >= start && cursor < end)
                            ?? lineRanges.find(({ end }) => cursor === end)
                            ?? lineRanges.reduce((nearest, range) => {
                                if (!nearest) return range;
                                const distance = cursor < range.start
                                    ? range.start - cursor
                                    : Math.max(0, cursor - range.end);
                                const nearestDistance = cursor < nearest.start
                                    ? nearest.start - cursor
                                    : Math.max(0, cursor - nearest.end);
                                return distance < nearestDistance ? range : nearest;
                            }, null);
                        setActiveTokenRows(activeRange ? [activeRange.row] : [], activeRange?.row ?? null, "auto", 2 / 3);
                    }
                }
                if (!update.docChanged) return;
                if (autoRunChk?.checked) scheduleAutoRun();
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

const selectionPointer = editorHost ? document.createElement("span") : null;
let selectionPointerPosition = null;
let selectionPointerFrame = null;
let selectionPointerAnimation = null;
let selectionBlinkFrame = null;
if (selectionPointer) {
    selectionPointer.className = "selection-pointer";
    selectionPointer.setAttribute("aria-hidden", "true");
    selectionPointer.hidden = true;
    editorHost.append(selectionPointer);
}

const updateSelectionPointer = () => {
    if (!editor || !selectionPointer || selectionPointer.hidden || selectionPointerPosition === null) return;
    if (selectionPointerFrame !== null) cancelAnimationFrame(selectionPointerFrame);
    selectionPointerFrame = requestAnimationFrame(() => {
        selectionPointerFrame = null;
        const position = Math.min(selectionPointerPosition, editor.state.doc.length);
        const coordinates = editor.coordsAtPos(position);
        const editorRect = editorHost.getBoundingClientRect();
        if (!coordinates || coordinates.bottom < editorRect.top || coordinates.top > editorRect.bottom
            || coordinates.left < editorRect.left || coordinates.left > editorRect.right) {
            selectionPointer.hidden = true;
            return;
        }

        selectionPointer.style.left = `${coordinates.left - editorRect.left}px`;
        selectionPointer.style.top = `${coordinates.bottom - editorRect.top + 1}px`;
    });
};

const pointToSelection = (start, end, isError = false) => {
    if (!selectionPointer) return;
    selectionPointer.classList.toggle("is-error", isError);
    selectionPointerPosition = end > start ? end : start;
    selectionPointer.hidden = false;
    selectionPointerAnimation?.cancel();
    updateSelectionPointer();
    const animation = selectionPointer.animate([
        { opacity: 0, offset: 0 },
        { opacity: 1, offset: 0.08 },
        { opacity: 0, offset: 0.16 },
        { opacity: 1, offset: 0.24 },
        { opacity: 0, offset: 0.32 },
        { opacity: 1, offset: 0.4 },
        { opacity: 0.82, offset: 0.48 },
        { opacity: 0.82, offset: 0.58 },
        { opacity: 0, offset: 1 },
    ], { duration: 2400, fill: "forwards" });
    selectionPointerAnimation = animation;
    animation.onfinish = () => {
        if (selectionPointerAnimation !== animation) return;
        selectionPointer.hidden = true;
        selectionPointerAnimation = null;
    };
};

if (editor) {
    editor.scrollDOM.addEventListener("scroll", updateSelectionPointer, { passive: true });
    window.addEventListener("resize", updateSelectionPointer);
    editor.dom.addEventListener("animationend", (event) => {
        if (event.animationName === "source-selection-blink") {
            editor.dom.classList.remove("cm-table-selection", "cm-error-selection");
        }
    });
}

const blinkSelectedText = (isError = false) => {
    if (!editor) return;
    editor.dom.classList.remove("cm-table-selection");
    editor.dom.classList.toggle("cm-error-selection", isError);
    if (selectionBlinkFrame !== null) cancelAnimationFrame(selectionBlinkFrame);
    selectionBlinkFrame = requestAnimationFrame(() => {
        selectionBlinkFrame = null;
        editor.dom.classList.add("cm-table-selection");
    });
};

if (lexerTableBody && editor) {
    lexerTableBody.addEventListener("click", (event) => {
        const row = event.target.closest("tr[data-start]");
        if (!row || !lexerTableBody.contains(row)) return;

        const start = Number(row.dataset.start);
        const end = Number(row.dataset.end);
        const docLength = editor.state.doc.length;
        const boundedStart = Math.min(start, docLength);
        editor.focus();
        editor.dispatch({
            selection: { anchor: boundedStart, head: Math.min(end, docLength) },
            effects: EditorView.scrollIntoView(boundedStart, { y: "center" }),
        });
        pointToSelection(boundedStart, Math.min(end, docLength));
        blinkSelectedText();
        setActiveTokenRows([row], row);
    });
}

document.getElementById("lexerbox")?.addEventListener("click", () => {
    activeErrorRow?.classList.remove("is-active");
    activeErrorRow = null;
});

if (errorTableBody && editor) {
    const focusErrorRow = (row) => {
        const docLength = editor.state.doc.length;
        const start = Math.min(Number(row.dataset.start), docLength);
        const end = Math.min(Number(row.dataset.end), docLength);
        editor.focus();
        editor.dispatch({
            selection: { anchor: start, head: end },
            effects: EditorView.scrollIntoView(start, { y: "center" }),
        });
        pointToSelection(start, end, true);
        blinkSelectedText(true);
        activeErrorRow?.classList.remove("is-active");
        row.classList.add("is-active");
        activeErrorRow = row;
    };

    errorTableBody.addEventListener("click", (event) => {
        const row = event.target.closest("tr[data-start]");
        if (row && errorTableBody.contains(row)) focusErrorRow(row);
    });

    errorTableBody.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        const row = event.target.closest("tr[data-start]");
        if (!row || !errorTableBody.contains(row)) return;
        event.preventDefault();
        focusErrorRow(row);
    });
}

/** Rebuild the table header to show/hide the optional Path column. */
function setTableColumns(showPath) {
    if (!lexerTableHead) return;
    const base = ["No.", "Lexeme", "Token", "Line", "Col"];
    if (showPath) base.push("Path");
    lexerTableHead.innerHTML = base.map((h) => `<th>${h}</th>`).join("");
}

function renderCompilerResult(result, source, trace) {
    const sourceLines = source.split("\n");
    const lineStarts = [];
    let sourceOffset = 0;
    sourceLines.forEach((line) => {
        lineStarts.push(sourceOffset);
        sourceOffset += line.length + 1;
    });

    const tokens = Array.isArray(result) ? result : result?.tokens;
    showErrors(result?.errors, lineStarts, sourceLines);
    setTableColumns(trace);
    tokenRanges = [];
    setActiveTokenRows([]);
    if (!lexerTableBody || !Array.isArray(tokens)) return;

    lexerTableBody.replaceChildren();
    if (tokens.length === 0) {
        const colSpan = trace ? 6 : 5;
        lexerTableBody.innerHTML = `<tr><td colspan="${colSpan}">No tokens</td></tr>`;
        return;
    }

    tokens.forEach(({ no, lexeme, token, line, column, path }) => {
        const row = document.createElement("tr");
        row.dataset.line = String(line);
        const range = getTokenRange(lineStarts, sourceLines, line, column, lexeme);
        if (range) {
            row.dataset.start = String(range.start);
            row.dataset.end = String(range.end);
            tokenRanges.push({ ...range, row });
        }
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

function saveOutputCache(source, result, skipComments, trace) {
    try {
        localStorage.setItem(outputStorageKey, JSON.stringify({
            version: 1,
            source,
            result,
            skipComments,
            trace,
        }));
    } catch (error) {
        console.warn("Could not cache lexer output:", error);
    }
}

function restoreOutputCache() {
    if (!editor) return;
    try {
        const cached = JSON.parse(localStorage.getItem(outputStorageKey) ?? "null");
        if (cached?.version !== 1 || cached.source !== editor.state.doc.toString()) return;

        const tokens = Array.isArray(cached.result) ? cached.result : cached.result?.tokens;
        if (!Array.isArray(tokens)) return;
        if (skipCommentsChk) skipCommentsChk.checked = Boolean(cached.skipComments);
        if (traceChk) traceChk.checked = Boolean(cached.trace);
        renderCompilerResult(cached.result, cached.source, Boolean(cached.trace));
    } catch (error) {
        console.warn("Could not restore lexer output:", error);
    }
}

if (runBtn) {
    if (autoRunChk) {
        runBtn.hidden = autoRunChk.checked;
        autoRunChk.addEventListener("change", () => {
            runBtn.hidden = autoRunChk.checked;
            if (autoRunChk.checked) {
                scheduleAutoRun();
            } else {
                window.clearTimeout(autoRunTimer);
                autoRunTimer = null;
                autoRunPending = false;
            }
        });

        [skipCommentsChk, traceChk].forEach((option) => {
            option?.addEventListener("change", () => {
                if (autoRunChk.checked) scheduleAutoRun();
            });
        });
    }

    runBtn.addEventListener("click", async () => {
        if (!editor) return;

        const skipComments = skipCommentsChk ? skipCommentsChk.checked : false;
        const trace = traceChk ? traceChk.checked : false;
        const source = editor.state.doc.toString();

        runBtn.disabled = true;
        try {
            const response = await fetch("./api.json", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    code: source,
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

            renderCompilerResult(result, source, trace);
            saveOutputCache(source, result, skipComments, trace);
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
            if (autoRunPending && autoRunChk?.checked) {
                autoRunPending = false;
                scheduleAutoRun();
            }
        }
    });
}

restoreOutputCache();

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
