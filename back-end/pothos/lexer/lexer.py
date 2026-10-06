"""
lexer.py - the Pothos lexical analyzer (hand-written state machine).

How to read this file next to the transition diagrams (TDs):

  * `state` holds a TD state number. State 0 is the shared start state.
      TD1 Reserved Words ............ states   1-136   -> _td1_reserved_words
      TD2 Reserved Symbols .......... states 137-195   -> _td2_reserved_symbols
      TD3 Identifiers ............... states 196-235   -> _td3_identifiers
      TD4 Integer Literals .......... states 236-271   -> _td4_integer_literals
      TD5 Strings and Comments ...... states 272-286   -> _td5_strings_comments
    A number used in two TDs is ONE state, so it has ONE branch here:
    141 "-", 149 "/", 153 "/-" (TD2 branches, with their TD4/TD5 edges) and
    192 '"', 194 "'" (numbered in TD2, edges drawn in TD5).

  * One `if state == N:` branch per non-final state. Inside it, one line per
    outgoing edge, tested against the edge label (a character or a set from
    charsets.py). Final states have no branch of their own: the delimiter edge
    calls self._accept(start, N, token_type), where N is the final state.

  * self._go(N) takes an edge: it consumes the current character and moves to
    state N.

  * Retraction: a final state marked * reads one character past the token (the
    delimiter) to know the token ended. That character is given back
    (retract 1), so it is read again as the start of the next token. State 154
    is marked ** and gives back 2 characters.

  * No matching edge = lexical error (B1). The error is recorded, the lexer
    skips to the next whitespace / delimiter, and continues, so one run reports
    every error.

Revisions to the TDs used here (details and page numbers in DECISIONS.md):
  A1  A TD1 state with no matching edge restarts at state 196 (TD3) from the
      first letter. So `ant`, `stri`, `belial1`, `pass` are identifiers.
  A2  TD5 multi-line comment: 282 loops on ml_char; 283 -ml_char-> 282;
      284 -'-'-> 284; 284 -ml_char_ns-> 282. The first --/ closes it.
  A3  delim_escape = { " ' \\ n t 0 } (from III.C.1.6).
  D   A COMPLETE reserved word followed by a character that is neither in its
      delimiter set nor a letter/digit/_ (e.g. `belial{`) is a lexical error.
      This is an open decision; see COMPLETE_KEYWORD_FALLS_BACK_TO_ID.
"""
from bisect import bisect_right
from typing import List, Tuple

from .charsets import (
    EOF, NEWLINE, TAB, SPACE,
    letter, digit, numbers, whitespace,
    ascii_str_dq, ascii_str_sq, ascii_comment_sl, ml_char, ml_char_ns,
    delim_space, delim_quote, delim_id, delim_int, delim_str, delim_close, delim_rbrace,
    delim_relop, delim_mathop, delim_minus, delim_assops, delim_colon, delim_reor,
    delim_flow, delim_mcomment_end, delim_bool, delim_block, delim_stmt,
    delim_open_paren, delim_open_brack, delim_open_brace, delim_comma, delim_term,
    delim_escape,
    alphanum_us, delim_minus_no_numbers, ascii_comment_sl_no_slash, newline_eof,
)
from .errors import LexicalError
from .tokens import (
    Token, ID, WHARFA_LIT, STRINA_LIT, TRUA_LIT, COMMENT_SL, COMMENT_ML,
)

# Open decision D (see DECISIONS.md). A complete reserved word followed by a
# character that is not in its delimiter set and is not a letter, digit or _
# (belial{  elsa(  reor;  lis[ ):
#   False -> lexical error. III.B.5: reserved words cannot be identifiers.
#   True  -> apply A1 literally: restart at 196, so `belial{` lexes as
#            id "belial" followed by "{" (the parser must reject it).
COMPLETE_KEYWORD_FALLS_BACK_TO_ID = False

END = -1        # pseudo-state: the current token is finished (accepted or error)

# Where error recovery stops skipping. Not a PDF set: whitespace (delim_space),
# the bracket/separator characters of delim_close, and the quotes (delim_quote),
# so a string right after a bad word is still lexed as a string.
RECOVERY_STOP = delim_space | {"(", ")", "{", "}", "[", "]", ";", ",", ":"} | delim_quote

# Error messages, with the PDF rule each one comes from.
ID_TOO_LONG = "identifier exceeds 20 characters (III.B.3)"
INT_TOO_LONG = "wharfa literal exceeds 8 significant digits (III.C.2.4)"
STR_RAW_NEWLINE = "unterminated strina literal: raw newline inside it, use \\n (III.C.1.5)"
STR_NO_CLOSE_DQ = 'unterminated strina literal: missing closing " (III.C.1.1)'
STR_NO_CLOSE_SQ = "unterminated strina literal: missing closing ' (III.C.1.1)"
ML_UNTERMINATED = "unterminated multi-line comment: missing '--/' (III.A.2.a)"
STRAY_CLOSER = "closing '--/' without an opening '/--' (III.A.2.b)"
UNDERSCORE_START = "invalid character '_': an identifier must begin with a letter (III.B.1.a)"


def tokenize(source: str, skip_comments: bool = False) -> Tuple[List[Token], List[LexicalError]]:
    """Lex Pothos source code.

    Returns (tokens, errors). Comments are returned as comment_sl / comment_ml
    tokens unless skip_comments=True. Errors never stop the lexer.
    """
    return Lexer(source, skip_comments=skip_comments).run()


def _show(c: str) -> str:
    """Describe a character for an error message."""
    if c == EOF:
        return "end of file"
    if c == NEWLINE:
        return "newline"
    if c == TAB:
        return "tab"
    if c == SPACE:
        return "space"
    return repr(c)


def _cannot_follow(c: str, what: str, set_name: str) -> str:
    return f"{_show(c)} cannot follow {what} (not in {set_name})"


def _not_ascii(c: str, where: str) -> str:
    return f"invalid character {_show(c)} in {where} (only ASCII characters are allowed)"


def _bad_escape(c: str) -> str:
    return f"invalid escape sequence '\\{c}' (III.C.1.6)"


class Lexer:
    def __init__(self, source: str, skip_comments: bool = False, trace: bool = False):
        self.src = source
        self.n = len(source)
        self.pos = 0                     # index of the next character to read
        self.skip_comments = skip_comments
        self.trace = trace               # record the state path of every token
        self.tokens: List[Token] = []
        self.errors: List[LexicalError] = []
        self.paths: List[Tuple[int, int, str, str]] = []   # (line, col, text, "0 -> 4 -> ...")
        self._line_starts = [0] + [i + 1 for i, ch in enumerate(source) if ch == NEWLINE]
        self._bad = False                # an error was found inside the current string/comment
        self._path: List[str] = []

    # ------------------------------------------------------------------ driver
    def run(self) -> Tuple[List[Token], List[LexicalError]]:
        while True:
            # Whitespace between tokens is skipped (it is a delimiter, not a token).
            while self.pos < self.n and self.src[self.pos] in whitespace:
                self.pos += 1
            if self.pos >= self.n:
                break
            self._scan_token()
        return self.tokens, self.errors

    def _scan_token(self) -> None:
        """Run the TDs from state 0 until one token is accepted or an error is recorded."""
        start = self.pos
        self._bad = False
        self._path = ["0"]
        state = 0
        while state != END:
            c = self._peek()
            if state == 0:
                state = self._state_0(c, start)
            elif state <= 136:
                state = self._td1_reserved_words(state, c, start)
            elif state in (192, 194):            # numbered in TD2, edges drawn in TD5
                state = self._td5_strings_comments(state, c, start)
            elif state <= 195:
                state = self._td2_reserved_symbols(state, c, start)
            elif state <= 235:
                state = self._td3_identifiers(state, c, start)
            elif state <= 271:
                state = self._td4_integer_literals(state, c, start)
            else:
                state = self._td5_strings_comments(state, c, start)

    # ----------------------------------------------------------------- helpers
    def _peek(self) -> str:
        """The current character, or EOF after the last one."""
        return self.src[self.pos] if self.pos < self.n else EOF

    def _go(self, next_state: int) -> int:
        """Take an edge: consume the current character and move to next_state."""
        self.pos += 1
        if self.trace:
            self._path.append(str(next_state))
        return next_state

    def _accept(self, start: int, final_state: int, token_type: str, retract: int = 1) -> int:
        """Take the delimiter edge into `final_state`, retract, and emit the token.

        The delimiter is consumed (EOF counts as one virtual character) and then
        given back: * = retract 1, ** = retract 2. self.pos then points at the
        first character that is NOT part of the token.
        """
        self.pos += 1               # read the delimiter
        self.pos -= retract         # give it back (and for **, one more)
        lexeme = self.src[start:self.pos]
        is_comment = token_type in (COMMENT_SL, COMMENT_ML)
        if not self._bad and not (is_comment and self.skip_comments):
            line, col = self._where(start)
            self.tokens.append(Token(token_type, lexeme, line, col))
        if self.trace:
            self._path.append(f"{final_state}{'*' * retract}")
            self._save_path(start, lexeme)
        return END

    def _error(self, start: int, message: str) -> int:
        """No matching edge (B1): record a lexical error, then recover.

        Recovery skips to the next character in RECOVERY_STOP (whitespace,
        brackets, separators, quotes), always skipping at least one character,
        and the next token starts there.
        """
        if self.pos == start:
            self.pos += 1
        while self.pos < self.n and self.src[self.pos] not in RECOVERY_STOP:
            self.pos += 1
        text = self.src[start:self.pos]
        line, col = self._where(start)
        self.errors.append(LexicalError(message, line, col, text))
        if self.trace:
            self._path.append("error")
            self._save_path(start, text)
        return END

    def _error_inside(self, back_to: int, message: str, text_start: int) -> int:
        """An error INSIDE a strina literal or comment (bad escape, non-ASCII char).

        Record it, then keep reading the literal/comment so its closing quote or
        end is still found. The literal/comment is not emitted as a token.
        """
        line, col = self._where(text_start)
        self.errors.append(LexicalError(message, line, col, self.src[text_start:self.pos + 1]))
        self._bad = True
        return self._go(back_to)

    def _restart_at_196(self, start: int) -> int:
        """A1: no matching TD1 edge -> restart at TD3 state 196 from the first letter."""
        self.pos = start + 1                 # the first letter is the edge 0 --letter--> 196
        if self.trace:
            self._path.append("A1->196")
        return 196

    def _keyword_not_delimited(self, start: int, word: str, set_name: str, c: str) -> int:
        """A complete reserved word (e.g. "belial") is NOT followed by its delimiter.

        * c is a letter, digit or _  -> A1: the word keeps going as an identifier
          (belial1, pass, prints, Trua2).
        * anything else (belial{)   -> D: lexical error (III.B.5), unless
          COMPLETE_KEYWORD_FALLS_BACK_TO_ID is True.
        """
        if c in alphanum_us or COMPLETE_KEYWORD_FALLS_BACK_TO_ID:
            return self._restart_at_196(start)
        return self._error(start, _cannot_follow(c, f"reserved word '{word}'", set_name))

    def _where(self, offset: int) -> Tuple[int, int]:
        """1-based (line, column) of a source offset."""
        line = bisect_right(self._line_starts, offset)
        return line, offset - self._line_starts[line - 1] + 1

    def _save_path(self, start: int, text: str) -> None:
        line, col = self._where(start)
        self.paths.append((line, col, text, " -> ".join(self._path)))

    # ================================================================ state 0
    def _state_0(self, c: str, start: int) -> int:
        """State 0: the shared start state of TD1-TD5."""
        # TD1: the first letter of a reserved word
        if c == "a": return self._go(1)                   # a
        if c == "b": return self._go(4)                   # b
        if c == "c": return self._go(14)                  # c
        if c == "d": return self._go(25)                  # d
        if c == "e": return self._go(31)                  # e
        if c == "f": return self._go(36)                  # f
        if c == "g": return self._go(42)                  # g
        if c == "i": return self._go(51)                  # i
        if c == "I": return self._go(65)                  # I
        if c == "l": return self._go(72)                  # l
        if c == "n": return self._go(80)                  # n
        if c == "o": return self._go(85)                  # o
        if c == "p": return self._go(91)                  # p
        if c == "r": return self._go(108)                 # r
        if c == "s": return self._go(113)                 # s
        if c == "t": return self._go(120)                 # t
        if c == "T": return self._go(125)                 # T
        if c == "w": return self._go(130)                 # w
        # TD3: any other letter starts an identifier
        if c in letter: return self._go(196)
        # TD4: integer literals
        if c == "0": return self._go(236)
        if c in digit: return self._go(238)
        # TD2: reserved symbols (" and ' continue in TD5)
        if c == "+": return self._go(137)
        if c == "-": return self._go(141)                 # also TD4 (negative) and TD5 (--)
        if c == "*": return self._go(145)
        if c == "/": return self._go(149)                 # also TD5 (/--)
        if c == "%": return self._go(155)
        if c == "<": return self._go(159)
        if c == ">": return self._go(163)
        if c == "=": return self._go(167)
        if c == "!": return self._go(171)
        if c == "(": return self._go(174)
        if c == ")": return self._go(176)
        if c == "[": return self._go(178)
        if c == "]": return self._go(180)
        if c == "{": return self._go(182)
        if c == "}": return self._go(184)
        if c == ",": return self._go(186)
        if c == ":": return self._go(188)
        if c == ";": return self._go(190)
        if c == '"': return self._go(192)
        if c == "'": return self._go(194)
        # no edge from state 0
        if c == "_":
            return self._error(start, UNDERSCORE_START)
        return self._error(start, f"invalid character {_show(c)}")

    # ============================================== TD1  Reserved Words 1-136
    def _td1_reserved_words(self, state: int, c: str, start: int) -> int:
        # Every final state is *: the delimiter is given back.
        # Trua (125-129) and Inaccu (65-71) produce the token type trua_lit.
        if state == 1:                                    # read "a"
            if c == "n": return self._go(2)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 2:                                    # read "an" (complete)
            if c in delim_flow: return self._accept(start, 3, "an")  # 2 -> 3*
            return self._keyword_not_delimited(start, "an", "delim_flow", c)  # A1 / D
        if state == 4:                                    # read "b"
            if c == "e": return self._go(5)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 5:                                    # read "be"
            if c == "l": return self._go(6)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 6:                                    # read "bel"
            if c == "i": return self._go(7)
            if c == "s": return self._go(11)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 7:                                    # read "beli"
            if c == "a": return self._go(8)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 8:                                    # read "belia"
            if c == "l": return self._go(9)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 9:                                    # read "belial" (complete)
            if c in delim_flow: return self._accept(start, 10, "belial")  # 9 -> 10*
            return self._keyword_not_delimited(start, "belial", "delim_flow", c)  # A1 / D
        if state == 11:                                   # read "bels"
            if c == "a": return self._go(12)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 12:                                   # read "belsa" (complete)
            if c in delim_flow: return self._accept(start, 13, "belsa")  # 12 -> 13*
            return self._keyword_not_delimited(start, "belsa", "delim_flow", c)  # A1 / D
        if state == 14:                                   # read "c"
            if c == "o": return self._go(15)
            if c == "y": return self._go(20)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 15:                                   # read "co"
            if c == "n": return self._go(16)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 16:                                   # read "con"
            if c == "s": return self._go(17)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 17:                                   # read "cons"
            if c == "t": return self._go(18)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 18:                                   # read "const" (complete)
            if c in delim_space: return self._accept(start, 19, "const")  # 18 -> 19*
            return self._keyword_not_delimited(start, "const", "delim_space", c)  # A1 / D
        if state == 20:                                   # read "cy"
            if c == "c": return self._go(21)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 21:                                   # read "cyc"
            if c == "l": return self._go(22)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 22:                                   # read "cycl"
            if c == "a": return self._go(23)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 23:                                   # read "cycla" (complete)
            if c in delim_flow: return self._accept(start, 24, "cycla")  # 23 -> 24*
            return self._keyword_not_delimited(start, "cycla", "delim_flow", c)  # A1 / D
        if state == 25:                                   # read "d"
            if c == "e": return self._go(26)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 26:                                   # read "de"
            if c == "l": return self._go(27)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 27:                                   # read "del"
            if c == "e": return self._go(28)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 28:                                   # read "dele"
            if c == "o": return self._go(29)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 29:                                   # read "deleo" (complete)
            if c in delim_space: return self._accept(start, 30, "deleo")  # 29 -> 30*
            return self._keyword_not_delimited(start, "deleo", "delim_space", c)  # A1 / D
        if state == 31:                                   # read "e"
            if c == "l": return self._go(32)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 32:                                   # read "el"
            if c == "s": return self._go(33)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 33:                                   # read "els"
            if c == "a": return self._go(34)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 34:                                   # read "elsa" (complete)
            if c in delim_block: return self._accept(start, 35, "elsa")  # 34 -> 35*
            return self._keyword_not_delimited(start, "elsa", "delim_block", c)  # A1 / D
        if state == 36:                                   # read "f"
            if c == "o": return self._go(37)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 37:                                   # read "fo"
            if c == "r": return self._go(38)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 38:                                   # read "for"
            if c == "m": return self._go(39)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 39:                                   # read "form"
            if c == "o": return self._go(40)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 40:                                   # read "formo" (complete)
            if c in delim_flow: return self._accept(start, 41, "formo")  # 40 -> 41*
            return self._keyword_not_delimited(start, "formo", "delim_flow", c)  # A1 / D
        if state == 42:                                   # read "g"
            if c == "l": return self._go(43)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 43:                                   # read "gl"
            if c == "o": return self._go(44)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 44:                                   # read "glo"
            if c == "s": return self._go(45)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 45:                                   # read "glos"
            if c == "s": return self._go(46)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 46:                                   # read "gloss"
            if c == "a": return self._go(47)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 47:                                   # read "glossa"
            if c == "r": return self._go(48)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 48:                                   # read "glossar"
            if c == "e": return self._go(49)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 49:                                   # read "glossare" (complete)
            if c in delim_space: return self._accept(start, 50, "glossare")  # 49 -> 50*
            return self._keyword_not_delimited(start, "glossare", "delim_space", c)  # A1 / D
        if state == 51:                                   # read "i"
            if c == "n": return self._go(52)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 52:                                   # read "in"
            if c == "n": return self._go(53)
            if c == "p": return self._go(57)
            if c == "s": return self._go(61)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 53:                                   # read "inn"
            if c == "u": return self._go(54)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 54:                                   # read "innu"
            if c == "m": return self._go(55)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 55:                                   # read "innum" (complete)
            if c in delim_flow: return self._accept(start, 56, "innum")  # 55 -> 56*
            return self._keyword_not_delimited(start, "innum", "delim_flow", c)  # A1 / D
        if state == 57:                                   # read "inp"
            if c == "u": return self._go(58)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 58:                                   # read "inpu"
            if c == "b": return self._go(59)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 59:                                   # read "inpub" (complete)
            if c in delim_flow: return self._accept(start, 60, "inpub")  # 59 -> 60*
            return self._keyword_not_delimited(start, "inpub", "delim_flow", c)  # A1 / D
        if state == 61:                                   # read "ins"
            if c == "i": return self._go(62)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 62:                                   # read "insi"
            if c == "d": return self._go(63)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 63:                                   # read "insid" (complete)
            if c in delim_space: return self._accept(start, 64, "insid")  # 63 -> 64*
            return self._keyword_not_delimited(start, "insid", "delim_space", c)  # A1 / D
        if state == 65:                                   # read "I"
            if c == "n": return self._go(66)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 66:                                   # read "In"
            if c == "a": return self._go(67)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 67:                                   # read "Ina"
            if c == "c": return self._go(68)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 68:                                   # read "Inac"
            if c == "c": return self._go(69)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 69:                                   # read "Inacc"
            if c == "u": return self._go(70)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 70:                                   # read "Inaccu" (complete)
            if c in delim_bool: return self._accept(start, 71, TRUA_LIT)  # 70 -> 71*
            return self._keyword_not_delimited(start, "Inaccu", "delim_bool", c)  # A1 / D
        if state == 72:                                   # read "l"
            if c == "i": return self._go(73)
            if c == "o": return self._go(76)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 73:                                   # read "li"
            if c == "s": return self._go(74)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 74:                                   # read "lis" (complete)
            if c in delim_space: return self._accept(start, 75, "lis")  # 74 -> 75*
            return self._keyword_not_delimited(start, "lis", "delim_space", c)  # A1 / D
        if state == 76:                                   # read "lo"
            if c == "o": return self._go(77)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 77:                                   # read "loo"
            if c == "d": return self._go(78)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 78:                                   # read "lood" (complete)
            if c in delim_flow: return self._accept(start, 79, "lood")  # 78 -> 79*
            return self._keyword_not_delimited(start, "lood", "delim_flow", c)  # A1 / D
        if state == 80:                                   # read "n"
            if c == "e": return self._go(81)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 81:                                   # read "ne"
            if c == "v": return self._go(82)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 82:                                   # read "nev"
            if c == "e": return self._go(83)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 83:                                   # read "neve" (complete)
            if c in delim_flow: return self._accept(start, 84, "neve")  # 83 -> 84*
            return self._keyword_not_delimited(start, "neve", "delim_flow", c)  # A1 / D
        if state == 85:                                   # read "o"
            if c == "t": return self._go(86)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 86:                                   # read "ot"
            if c == "h": return self._go(87)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 87:                                   # read "oth"
            if c == "a": return self._go(88)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 88:                                   # read "otha"
            if c == "n": return self._go(89)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 89:                                   # read "othan" (complete)
            if c in delim_flow: return self._accept(start, 90, "othan")  # 89 -> 90*
            return self._keyword_not_delimited(start, "othan", "delim_flow", c)  # A1 / D
        if state == 91:                                   # read "p"
            if c == "a": return self._go(92)
            if c == "e": return self._go(98)
            if c == "r": return self._go(104)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 92:                                   # read "pa"
            if c == "s": return self._go(93)
            if c == "u": return self._go(95)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 93:                                   # read "pas" (complete)
            if c in delim_stmt: return self._accept(start, 94, "pas")  # 93 -> 94*
            return self._keyword_not_delimited(start, "pas", "delim_stmt", c)  # A1 / D
        if state == 95:                                   # read "pau"
            if c == "s": return self._go(96)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 96:                                   # read "paus" (complete)
            if c in delim_stmt: return self._accept(start, 97, "paus")  # 96 -> 97*
            return self._keyword_not_delimited(start, "paus", "delim_stmt", c)  # A1 / D
        if state == 98:                                   # read "pe"
            if c == "r": return self._go(99)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 99:                                   # read "per"
            if c == "s": return self._go(100)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 100:                                  # read "pers"
            if c == "i": return self._go(101)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 101:                                  # read "persi"
            if c == "s": return self._go(102)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 102:                                  # read "persis" (complete)
            if c in delim_stmt: return self._accept(start, 103, "persis")  # 102 -> 103*
            return self._keyword_not_delimited(start, "persis", "delim_stmt", c)  # A1 / D
        if state == 104:                                  # read "pr"
            if c == "i": return self._go(105)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 105:                                  # read "pri"
            if c == "n": return self._go(106)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 106:                                  # read "prin" (complete)
            if c in delim_flow: return self._accept(start, 107, "prin")  # 106 -> 107*
            return self._keyword_not_delimited(start, "prin", "delim_flow", c)  # A1 / D
        if state == 108:                                  # read "r"
            if c == "e": return self._go(109)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 109:                                  # read "re"
            if c == "o": return self._go(110)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 110:                                  # read "reo"
            if c == "r": return self._go(111)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 111:                                  # read "reor" (complete)
            if c in delim_reor: return self._accept(start, 112, "reor")  # 111 -> 112*
            return self._keyword_not_delimited(start, "reor", "delim_reor", c)  # A1 / D
        if state == 113:                                  # read "s"
            if c == "t": return self._go(114)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 114:                                  # read "st"
            if c == "r": return self._go(115)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 115:                                  # read "str"
            if c == "i": return self._go(116)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 116:                                  # read "stri"
            if c == "n": return self._go(117)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 117:                                  # read "strin"
            if c == "a": return self._go(118)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 118:                                  # read "strina" (complete)
            if c in delim_space: return self._accept(start, 119, "strina")  # 118 -> 119*
            return self._keyword_not_delimited(start, "strina", "delim_space", c)  # A1 / D
        if state == 120:                                  # read "t"
            if c == "r": return self._go(121)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 121:                                  # read "tr"
            if c == "u": return self._go(122)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 122:                                  # read "tru"
            if c == "a": return self._go(123)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 123:                                  # read "trua" (complete)
            if c in delim_space: return self._accept(start, 124, "trua")  # 123 -> 124*
            return self._keyword_not_delimited(start, "trua", "delim_space", c)  # A1 / D
        if state == 125:                                  # read "T"
            if c == "r": return self._go(126)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 126:                                  # read "Tr"
            if c == "u": return self._go(127)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 127:                                  # read "Tru"
            if c == "a": return self._go(128)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 128:                                  # read "Trua" (complete)
            if c in delim_bool: return self._accept(start, 129, TRUA_LIT)  # 128 -> 129*
            return self._keyword_not_delimited(start, "Trua", "delim_bool", c)  # A1 / D
        if state == 130:                                  # read "w"
            if c == "h": return self._go(131)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 131:                                  # read "wh"
            if c == "a": return self._go(132)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 132:                                  # read "wha"
            if c == "r": return self._go(133)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 133:                                  # read "whar"
            if c == "f": return self._go(134)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 134:                                  # read "wharf"
            if c == "a": return self._go(135)
            return self._restart_at_196(start)            # A1: not a reserved word
        if state == 135:                                  # read "wharfa" (complete)
            if c in delim_space: return self._accept(start, 136, "wharfa")  # 135 -> 136*
            return self._keyword_not_delimited(start, "wharfa", "delim_space", c)  # A1 / D
        raise AssertionError(f"unknown TD1 state {state}")

    # ============================================ TD2  Reserved Symbols 137-195
    def _td2_reserved_symbols(self, state: int, c: str, start: int) -> int:
        # Every final state is * except 154 (**).
        if state == 137:                                  # read "+"
            if c == "=":          return self._go(139)
            if c in delim_mathop: return self._accept(start, 138, "+")         # 137 -> 138*
            return self._error(start, _cannot_follow(c, "'+'", "delim_mathop"))
        if state == 139:                                  # read "+="
            if c in delim_assops: return self._accept(start, 140, "+=")        # 139 -> 140*
            return self._error(start, _cannot_follow(c, "'+='", "delim_assops"))

        if state == 141:                                  # read "-"  (shared: TD2, TD4, TD5)
            if c == "=":                    return self._go(143)               # TD2: -=
            if c == "-":                    return self._go(278)               # TD5: -- comment
            if c == "0":                    return self._go(254)               # TD4: -0...
            if c in digit:                  return self._go(256)               # TD4: -digit...
            if c in delim_minus_no_numbers: return self._accept(start, 142, "-")   # 141 -> 142*
            return self._error(start, _cannot_follow(c, "'-'", "delim_minus"))
        if state == 143:                                  # read "-="
            if c in delim_assops: return self._accept(start, 144, "-=")        # 143 -> 144*
            return self._error(start, _cannot_follow(c, "'-='", "delim_assops"))

        if state == 145:                                  # read "*"
            if c == "=":          return self._go(147)
            if c in delim_mathop: return self._accept(start, 146, "*")         # 145 -> 146*
            return self._error(start, _cannot_follow(c, "'*'", "delim_mathop"))
        if state == 147:                                  # read "*="
            if c in delim_assops: return self._accept(start, 148, "*=")        # 147 -> 148*
            return self._error(start, _cannot_follow(c, "'*='", "delim_assops"))

        if state == 149:                                  # read "/"  (shared: TD2, TD5)
            if c == "=":          return self._go(151)
            if c == "-":          return self._go(153)
            if c in delim_minus:  return self._accept(start, 150, "/")         # 149 -> 150*
            return self._error(start, _cannot_follow(c, "'/'", "delim_minus"))
        if state == 151:                                  # read "/="
            if c in delim_assops: return self._accept(start, 152, "/=")        # 151 -> 152*
            return self._error(start, _cannot_follow(c, "'/='", "delim_assops"))
        if state == 153:                                  # read "/-"  (shared: TD2, TD5)
            if c == "-":          return self._go(282)                         # TD5: /-- comment
            # 154**: "/" then "-" then a delim_minus character (10/-2, a/-b).
            # Give back 2 characters ("-" and c), emit "/"; the "-" is read again.
            if c in delim_minus:  return self._accept(start, 154, "/", retract=2)
            return self._error(start, _cannot_follow(c, "'-'", "delim_minus"))

        if state == 155:                                  # read "%"
            if c == "=":          return self._go(157)
            if c in delim_mathop: return self._accept(start, 156, "%")         # 155 -> 156*
            return self._error(start, _cannot_follow(c, "'%'", "delim_mathop"))
        if state == 157:                                  # read "%="
            if c in delim_assops: return self._accept(start, 158, "%=")        # 157 -> 158*
            return self._error(start, _cannot_follow(c, "'%='", "delim_assops"))

        if state == 159:                                  # read "<"
            if c == "=":          return self._go(161)
            if c in delim_relop:  return self._accept(start, 160, "<")         # 159 -> 160*
            return self._error(start, _cannot_follow(c, "'<'", "delim_relop"))
        if state == 161:                                  # read "<="
            if c in delim_relop:  return self._accept(start, 162, "<=")        # 161 -> 162*
            return self._error(start, _cannot_follow(c, "'<='", "delim_relop"))

        if state == 163:                                  # read ">"
            if c == "=":          return self._go(165)
            if c in delim_relop:  return self._accept(start, 164, ">")         # 163 -> 164*
            return self._error(start, _cannot_follow(c, "'>'", "delim_relop"))
        if state == 165:                                  # read ">="
            if c in delim_relop:  return self._accept(start, 166, ">=")        # 165 -> 166*
            return self._error(start, _cannot_follow(c, "'>='", "delim_relop"))

        if state == 167:                                  # read "="
            if c == "=":          return self._go(169)
            if c in delim_assops: return self._accept(start, 168, "=")         # 167 -> 168*
            return self._error(start, _cannot_follow(c, "'='", "delim_assops"))
        if state == 169:                                  # read "=="
            if c in delim_relop:  return self._accept(start, 170, "==")        # 169 -> 170*
            return self._error(start, _cannot_follow(c, "'=='", "delim_relop"))

        if state == 171:                                  # read "!"
            if c == "=":          return self._go(172)
            return self._error(start, f"'!' must be followed by '=' (found {_show(c)})")
        if state == 172:                                  # read "!="
            if c in delim_relop:  return self._accept(start, 173, "!=")        # 172 -> 173*
            return self._error(start, _cannot_follow(c, "'!='", "delim_relop"))

        if state == 174:                                  # read "("
            if c in delim_open_paren: return self._accept(start, 175, "(")     # 174 -> 175*
            return self._error(start, _cannot_follow(c, "'('", "delim_open_paren"))
        if state == 176:                                  # read ")"
            if c in delim_close:      return self._accept(start, 177, ")")     # 176 -> 177*
            return self._error(start, _cannot_follow(c, "')'", "delim_close"))
        if state == 178:                                  # read "["
            if c in delim_open_brack: return self._accept(start, 179, "[")     # 178 -> 179*
            return self._error(start, _cannot_follow(c, "'['", "delim_open_brack"))
        if state == 180:                                  # read "]"
            if c in delim_close:      return self._accept(start, 181, "]")     # 180 -> 181*
            return self._error(start, _cannot_follow(c, "']'", "delim_close"))
        if state == 182:                                  # read "{"
            if c in delim_open_brace: return self._accept(start, 183, "{")     # 182 -> 183*
            return self._error(start, _cannot_follow(c, "'{'", "delim_open_brace"))
        if state == 184:                                  # read "}"
            if c in delim_rbrace:     return self._accept(start, 185, "}")     # 184 -> 185*
            return self._error(start, _cannot_follow(c, "'}'", "delim_rbrace"))

        if state == 186:                                  # read ","
            if c in delim_comma:      return self._accept(start, 187, ",")     # 186 -> 187*
            return self._error(start, _cannot_follow(c, "','", "delim_comma"))
        if state == 188:                                  # read ":"
            if c in delim_colon:      return self._accept(start, 189, ":")     # 188 -> 189*
            return self._error(start, _cannot_follow(c, "':'", "delim_colon"))
        if state == 190:                                  # read ";"
            if c in delim_term:       return self._accept(start, 191, ";")     # 190 -> 191*
            return self._error(start, _cannot_follow(c, "';'", "delim_term"))

        # 192 and 194 (the opening quotes) are handled in _td5_strings_comments.
        # TD2 also draws 192 --delim_dquote--> 193* and 194 --delim_squote--> 195*.
        # delim_dquote = ascii_str_dq + { \ " } is exactly the set of characters
        # that TD5 gives an edge out of 192 (same for 194), so the TD5 edges are
        # used and 193 / 195 are never reached: no separate quote token (B3).
        raise AssertionError(f"unknown TD2 state {state}")

    # ================================================= TD3  Identifiers 196-235
    def _td3_identifiers(self, state: int, c: str, start: int) -> int:
        # identifier = letter (alphanum | _){0,19}: 1 to 20 characters.
        # State 196 + 2(k-1) means "k characters read"; its final state is the next number.
        if state == 196:                                  # 1 character
            if c in alphanum_us: return self._go(198)
            if c in delim_id:    return self._accept(start, 197, ID)  # 196 -> 197*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 198:                                  # 2 characters
            if c in alphanum_us: return self._go(200)
            if c in delim_id:    return self._accept(start, 199, ID)  # 198 -> 199*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 200:                                  # 3 characters
            if c in alphanum_us: return self._go(202)
            if c in delim_id:    return self._accept(start, 201, ID)  # 200 -> 201*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 202:                                  # 4 characters
            if c in alphanum_us: return self._go(204)
            if c in delim_id:    return self._accept(start, 203, ID)  # 202 -> 203*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 204:                                  # 5 characters
            if c in alphanum_us: return self._go(206)
            if c in delim_id:    return self._accept(start, 205, ID)  # 204 -> 205*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 206:                                  # 6 characters
            if c in alphanum_us: return self._go(208)
            if c in delim_id:    return self._accept(start, 207, ID)  # 206 -> 207*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 208:                                  # 7 characters
            if c in alphanum_us: return self._go(210)
            if c in delim_id:    return self._accept(start, 209, ID)  # 208 -> 209*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 210:                                  # 8 characters
            if c in alphanum_us: return self._go(212)
            if c in delim_id:    return self._accept(start, 211, ID)  # 210 -> 211*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 212:                                  # 9 characters
            if c in alphanum_us: return self._go(214)
            if c in delim_id:    return self._accept(start, 213, ID)  # 212 -> 213*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 214:                                  # 10 characters
            if c in alphanum_us: return self._go(216)
            if c in delim_id:    return self._accept(start, 215, ID)  # 214 -> 215*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 216:                                  # 11 characters
            if c in alphanum_us: return self._go(218)
            if c in delim_id:    return self._accept(start, 217, ID)  # 216 -> 217*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 218:                                  # 12 characters
            if c in alphanum_us: return self._go(220)
            if c in delim_id:    return self._accept(start, 219, ID)  # 218 -> 219*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 220:                                  # 13 characters
            if c in alphanum_us: return self._go(222)
            if c in delim_id:    return self._accept(start, 221, ID)  # 220 -> 221*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 222:                                  # 14 characters
            if c in alphanum_us: return self._go(224)
            if c in delim_id:    return self._accept(start, 223, ID)  # 222 -> 223*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 224:                                  # 15 characters
            if c in alphanum_us: return self._go(226)
            if c in delim_id:    return self._accept(start, 225, ID)  # 224 -> 225*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 226:                                  # 16 characters
            if c in alphanum_us: return self._go(228)
            if c in delim_id:    return self._accept(start, 227, ID)  # 226 -> 227*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 228:                                  # 17 characters
            if c in alphanum_us: return self._go(230)
            if c in delim_id:    return self._accept(start, 229, ID)  # 228 -> 229*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 230:                                  # 18 characters
            if c in alphanum_us: return self._go(232)
            if c in delim_id:    return self._accept(start, 231, ID)  # 230 -> 231*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 232:                                  # 19 characters
            if c in alphanum_us: return self._go(234)
            if c in delim_id:    return self._accept(start, 233, ID)  # 232 -> 233*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 234:                                  # 20 characters (the maximum)
            if c in delim_id:    return self._accept(start, 235, ID)  # 234 -> 235*
            if c in alphanum_us: return self._error(start, ID_TOO_LONG)  # no edge for a 21st character
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        raise AssertionError(f"unknown TD3 state {state}")

    # ============================================ TD4  Integer Literals 236-271
    def _td4_integer_literals(self, state: int, c: str, start: int) -> int:
        # wharfa_lit: leading zeros (236 / 254 loops) do not count; then 1-8
        # significant digits. Negatives come from the shared "-" state 141 (TD2).
        # ---- positive: 0 --0--> 236, 0 --digit--> 238 ----
        if state == 236:                                  # read "0", "00", ...  leading zeros do not count
            if c == "0":       return self._go(236)       # loop on 0
            if c in digit:     return self._go(238)
            if c in delim_int: return self._accept(start, 237, WHARFA_LIT)  # 236 -> 237*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 238:                                  # 1 significant digit
            if c in numbers:   return self._go(240)
            if c in delim_int: return self._accept(start, 239, WHARFA_LIT)  # 238 -> 239*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 240:                                  # 2 significant digits
            if c in numbers:   return self._go(242)
            if c in delim_int: return self._accept(start, 241, WHARFA_LIT)  # 240 -> 241*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 242:                                  # 3 significant digits
            if c in numbers:   return self._go(244)
            if c in delim_int: return self._accept(start, 243, WHARFA_LIT)  # 242 -> 243*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 244:                                  # 4 significant digits
            if c in numbers:   return self._go(246)
            if c in delim_int: return self._accept(start, 245, WHARFA_LIT)  # 244 -> 245*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 246:                                  # 5 significant digits
            if c in numbers:   return self._go(248)
            if c in delim_int: return self._accept(start, 247, WHARFA_LIT)  # 246 -> 247*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 248:                                  # 6 significant digits
            if c in numbers:   return self._go(250)
            if c in delim_int: return self._accept(start, 249, WHARFA_LIT)  # 248 -> 249*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 250:                                  # 7 significant digits
            if c in numbers:   return self._go(252)
            if c in delim_int: return self._accept(start, 251, WHARFA_LIT)  # 250 -> 251*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 252:                                  # 8 significant digits (the maximum)
            if c in delim_int: return self._accept(start, 253, WHARFA_LIT)  # 252 -> 253*
            if c in numbers:   return self._error(start, INT_TOO_LONG)  # no edge for a 9th digit
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))

        # ---- negative (shared state 141 from TD2): 141 --0--> 254, 141 --digit--> 256 ----
        if state == 254:                                  # read "-0", "-00", ...  leading zeros do not count
            if c == "0":       return self._go(254)       # loop on 0
            if c in digit:     return self._go(256)
            if c in delim_int: return self._accept(start, 255, WHARFA_LIT)  # 254 -> 255*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 256:                                  # -1 significant digit
            if c in numbers:   return self._go(258)
            if c in delim_int: return self._accept(start, 257, WHARFA_LIT)  # 256 -> 257*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 258:                                  # -2 significant digits
            if c in numbers:   return self._go(260)
            if c in delim_int: return self._accept(start, 259, WHARFA_LIT)  # 258 -> 259*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 260:                                  # -3 significant digits
            if c in numbers:   return self._go(262)
            if c in delim_int: return self._accept(start, 261, WHARFA_LIT)  # 260 -> 261*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 262:                                  # -4 significant digits
            if c in numbers:   return self._go(264)
            if c in delim_int: return self._accept(start, 263, WHARFA_LIT)  # 262 -> 263*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 264:                                  # -5 significant digits
            if c in numbers:   return self._go(266)
            if c in delim_int: return self._accept(start, 265, WHARFA_LIT)  # 264 -> 265*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 266:                                  # -6 significant digits
            if c in numbers:   return self._go(268)
            if c in delim_int: return self._accept(start, 267, WHARFA_LIT)  # 266 -> 267*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 268:                                  # -7 significant digits
            if c in numbers:   return self._go(270)
            if c in delim_int: return self._accept(start, 269, WHARFA_LIT)  # 268 -> 269*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        if state == 270:                                  # -8 significant digits (the maximum)
            if c in delim_int: return self._accept(start, 271, WHARFA_LIT)  # 270 -> 271*
            if c in numbers:   return self._error(start, INT_TOO_LONG)  # no edge for a 9th digit
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_int"))
        raise AssertionError(f"unknown TD4 state {state}")

    # ================================= TD5  String Literals and Comments 272-286
    def _td5_strings_comments(self, state: int, c: str, start: int) -> int:
        # ---- strina literal in double quotes: 0 --"--> 192 ----
        if state == 192:                                  # inside "..."
            if c == '"':          return self._go(272)    # closing quote
            if c == "\\":         return self._go(274)    # start of an escape
            if c in ascii_str_dq: return self._go(192)    # loop
            if c == NEWLINE:      return self._error(start, STR_RAW_NEWLINE)
            if c == EOF:          return self._error(start, STR_NO_CLOSE_DQ)
            return self._error_inside(192, _not_ascii(c, "a strina literal"), self.pos)
        if state == 274:                                  # read "\" inside "..."
            if c in delim_escape: return self._go(192)    # \" \' \\ \n \t \0
            if c in newline_eof:  return self._error(start, STR_NO_CLOSE_DQ)
            return self._error_inside(192, _bad_escape(c), self.pos - 1)
        if state == 272:                                  # read the closing "
            if c in delim_str:    return self._accept(start, 273, STRINA_LIT)       # 272 -> 273*
            return self._error(start, _cannot_follow(c, "a strina literal", "delim_str"))

        # ---- strina literal in single quotes: 0 --'--> 194 ----
        if state == 194:                                  # inside '...'
            if c == "'":          return self._go(275)    # closing quote
            if c == "\\":         return self._go(277)    # start of an escape
            if c in ascii_str_sq: return self._go(194)    # loop
            if c == NEWLINE:      return self._error(start, STR_RAW_NEWLINE)
            if c == EOF:          return self._error(start, STR_NO_CLOSE_SQ)
            return self._error_inside(194, _not_ascii(c, "a strina literal"), self.pos)
        if state == 277:                                  # read "\" inside '...'
            if c in delim_escape: return self._go(194)
            if c in newline_eof:  return self._error(start, STR_NO_CLOSE_SQ)
            return self._error_inside(194, _bad_escape(c), self.pos - 1)
        if state == 275:                                  # read the closing '
            if c in delim_str:    return self._accept(start, 276, STRINA_LIT)       # 275 -> 276*
            return self._error(start, _cannot_follow(c, "a strina literal", "delim_str"))

        # ---- single-line comment: 0 --'-'--> 141 --'-'--> 278 ----
        if state == 278:                                  # read "--"
            if c in newline_eof:               return self._accept(start, 279, COMMENT_SL)   # 278 -> 279*
            if c in ascii_comment_sl_no_slash: return self._go(280)
            if c == "/":                       return self._error(start, STRAY_CLOSER)
            return self._error_inside(280, _not_ascii(c, "a comment"), self.pos)
        if state == 280:                                  # inside "-- ..."
            if c in ascii_comment_sl:          return self._go(280)                          # loop
            if c in newline_eof:               return self._accept(start, 281, COMMENT_SL)   # 280 -> 281*
            return self._error_inside(280, _not_ascii(c, "a comment"), self.pos)

        # ---- multi-line comment: 0 --/--> 149 --'-'--> 153 --'-'--> 282 (A2 edges) ----
        if state == 282:                                  # inside "/-- ..."
            if c == "-":          return self._go(283)
            if c in ml_char:      return self._go(282)    # loop (A2: ml_char, not "ascii, newline")
            if c == EOF:          return self._error(start, ML_UNTERMINATED)
            return self._error_inside(282, _not_ascii(c, "a comment"), self.pos)
        if state == 283:                                  # read "-" inside the comment
            if c == "-":          return self._go(284)
            if c in ml_char:      return self._go(282)    # A2: a lone "-" is comment text
            if c == EOF:          return self._error(start, ML_UNTERMINATED)
            return self._error_inside(282, _not_ascii(c, "a comment"), self.pos)
        if state == 284:                                  # read "--" inside the comment
            if c == "/":          return self._go(285)    # the FIRST --/ closes (III.A.2.c)
            if c == "-":          return self._go(284)    # A2: "---/" still closes
            if c in ml_char_ns:   return self._go(282)    # A2: "--x" is comment text
            if c == EOF:          return self._error(start, ML_UNTERMINATED)
            return self._error_inside(282, _not_ascii(c, "a comment"), self.pos)
        if state == 285:                                  # read the closing "--/"
            if c in delim_mcomment_end: return self._accept(start, 286, COMMENT_ML)    # 285 -> 286*
            return self._error(start, _cannot_follow(c, "'--/'", "delim_mcomment_end"))

        raise AssertionError(f"unknown TD5 state {state}")
