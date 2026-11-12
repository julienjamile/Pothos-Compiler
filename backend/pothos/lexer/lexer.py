"""
lexer.py - the Pothos lexical analyzer (hand-written state machine).

How to read this file alongside the transition diagrams:

  * `state` holds a TD state number. State 0 is the shared start state.
      TD1 Reserved Words ............ states   1-143   -> _td1_reserved_words
      TD2 Reserved Symbols .......... states 144-199   -> _td2_reserved_symbols
      TD3 Identifiers ............... states 200-240   -> _td3_identifiers
      TD4 Integer and Float Literals  states 241-268   -> _td4_integer_literals
      TD5 Strings and Comments ...... states 269-281   -> _td5_strings_comments
    A number used in two TDs is ONE state, so it has ONE branch here:
    148 "-", 157 "/", 161 "/-" (TD2 branches, with their TD5 edges) and
    269 '"', 272 "'" (opening quote states drawn in TD5).

  * One `if state == N:` branch per non-final state. Inside it, one line per
    outgoing edge, tested against the edge label (a character or a set from
    charsets.py). Final states have no branch of their own: the delimiter edge
    calls self._accept(start, N, token_type), where N is the final state.

  * self._go(N) takes an edge: it consumes the current character and moves to
    state N.

  * Retraction: a final state marked * reads one character past the token (the
    delimiter) to know the token ended. That character is given back
    (retract 1), so it is read again as the start of the next token. State 162
    is marked ** and gives back 2 characters.

  * No matching edge = lexical error. The error is recorded, the lexer
    skips to the next whitespace / delimiter, and continues, so one run reports
    every error.

Behavioral choices and examples are described in DECISIONS.md.
"""
from bisect import bisect_right
from typing import List, Tuple

from .charsets import (
    EOF, NEWLINE, TAB, SPACE,
    letter, digit, numbers, whitespace, ascii, escape,
    delim_space, delim_quote, delim_id, delim_num, delim_bool, delim_block, delim_stmt,
    delim_openparen, delim_openbracket, delim_opencurly, delim_closeparen,
    delim_closebracket, delim_closecurly, delim_comma, delim_colon, delim_scolon,
    delim_datatype, delim_io, delim_logic, delim_logic_newline, delim_struc, delim_deleo, delim_const,
    delim_insid,
    delim_plus, delim_arithmetic, delim_oper, delim_equality,
    delim_equal, delim_augoper, delim_dqopen, delim_dqclose, delim_sqopen,
    delim_sqclose, delim_slcomment, delim_mlcomment_open, delim_mlcomment_close,
    alphanum_us,
)
from .errors import LexicalError
from .tokens import (
    Token, ID, WHARFA_LIT, FLO_LIT, STRINA_LIT, TRUA_LIT, COMMENT_SL, COMMENT_ML,
    SPACE_TOKEN, NEWLINE_TOKEN, TAB_TOKEN,
)

# A complete reserved word followed by a
# character that is not in its delimiter set and is not a letter, digit or _
# (belial{  elsa(  reor;  lis[ ):
#   False -> lexical error.
#   True  -> restart at 200, so `belial{` lexes as
#            id "belial" followed by "{" (the parser must reject it).
COMPLETE_KEYWORD_FALLS_BACK_TO_ID = False

END = -1        # pseudo-state: the current token is finished (accepted or error)

# Recovery stops at whitespace, brackets, separators, and quotes so strings remain visible.
RECOVERY_STOP = delim_space | {"(", ")", "{", "}", "[", "]", ";", ",", ":"} | delim_quote
ID_DELIMITER = delim_id  # EOF is not an identifier delimiter in the current QA table.
REOR_DELIMITER = delim_struc - {NEWLINE, ";"} | delim_quote
INSID_DELIMITER = delim_insid & delim_space

# Error messages describe the violated lexical rule.
ID_TOO_LONG = "identifier exceeds 20 characters"
INT_TOO_LONG = "wharfa literal exceeds 8 significant digits"
STR_NO_CLOSE_DQ = 'unterminated strina literal: missing closing "'
STR_NO_CLOSE_SQ = "unterminated strina literal: missing closing '"
ML_UNTERMINATED = "unterminated multi-line comment: missing '--/'"
STRAY_CLOSER = "closing '--/' without an opening '/--'"
UNDERSCORE_START = "invalid character '_': an identifier must begin with a letter"


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
    return f"invalid escape sequence '\\{c}'"


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
        while self.pos < self.n:
            c = self.src[self.pos]
            if c in (SPACE, NEWLINE, TAB):
                start = self.pos
                if c == SPACE:
                    token_type = SPACE_TOKEN
                elif c == TAB:
                    token_type = TAB_TOKEN
                else:
                    token_type = NEWLINE_TOKEN
                line, col = self._where(start)
                self.tokens.append(Token(token_type, c, line, col))
                if self.trace:
                    self.paths.append((line, col, c, f"whitespace -> {token_type}"))
                self.pos += 1
                continue
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
            if c != EOF and c not in ascii and c != NEWLINE:
                if state == 269:
                    state = self._error_inside(269, _not_ascii(c, "source"), self.pos)
                elif state == 272:
                    state = self._error_inside(272, _not_ascii(c, "source"), self.pos)
                elif state == 301:
                    state = self._error_non_ascii_escape(c, 269)
                elif state == 302:
                    state = self._error_non_ascii_escape(c, 272)
                elif state == 275:
                    state = self._error_inside(275, _not_ascii(c, "source"), self.pos)
                elif state in (277, 278, 279):
                    state = self._error_inside(277, _not_ascii(c, "source"), self.pos)
                elif state == 270:
                    state = self._accept(start, 271, STRINA_LIT)
                elif state == 273:
                    state = self._accept(start, 274, STRINA_LIT)
                elif state == 280:
                    state = self._accept(start, 281, COMMENT_ML)
                else:
                    state = self._error_character(c)
                continue
            if state == 0:
                state = self._state_0(c, start)
            elif 1 <= state <= 143:
                state = self._td1_reserved_words(state, c, start)
            elif state in (269, 272, 301, 302):
                state = self._td5_strings_comments(state, c, start)
            elif 144 <= state <= 199:
                state = self._td2_reserved_symbols(state, c, start)
            elif 200 <= state <= 240:
                state = self._td3_identifiers(state, c, start)
            elif 241 <= state <= 268 or state == 300:
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
        source_lexeme = self.src[start:self.pos]
        lexeme = source_lexeme
        is_comment = token_type in (COMMENT_SL, COMMENT_ML)
        if not self._bad and not (is_comment and self.skip_comments):
            line, col = self._where(start)
            value = None
            if token_type == FLO_LIT:
                # Round exactly to four places and normalize the token-table
                # spelling. Fractional zeroes are trimmed, with at least .0.
                whole, fraction = source_lexeme.split(".", 1)
                whole = whole.lstrip("0") or "0"
                fraction4 = fraction[:4].ljust(4, "0")
                scaled = int(whole) * 10_000 + int(fraction4)
                if len(fraction) > 4 and fraction[4] >= "5":
                    scaled += 1
                whole_value, fractional_value = divmod(scaled, 10_000)
                fractional_text = f"{fractional_value:04d}".rstrip("0") or "0"
                lexeme = f"{whole_value}.{fractional_text}"
                value = float(lexeme)
            elif token_type == WHARFA_LIT:
                lexeme = source_lexeme.lstrip("0") or "0"
                value = int(lexeme)
            self.tokens.append(Token(token_type, lexeme, line, col, value))
        if self.trace:
            self._path.append(f"{final_state}{'*' * retract}")
            self._save_path(start, source_lexeme)
        return END

    def _error(self, start: int, message: str) -> int:
        """No matching edge: record a lexical error, then recover.

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

    def _overflow_error(self, start: int, message: str) -> int:
        """Report the overlength prefix and leave its first excess character unread.

        The next scan starts at that excess character. This mirrors the TD
        overflow edge: the prefix is rejected, while the suffix can still form
        a separate token.
        """
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

    def _error_non_ascii_escape(self, c: str, back_to: int) -> int:
        slash = self.pos - 1
        line, col = self._where(slash)
        self.errors.append(LexicalError(_bad_escape(c), line, col, self.src[slash:self.pos + 1]))
        self._bad = True
        line, col = self._where(self.pos)
        self.errors.append(LexicalError(_not_ascii(c, "source"), line, col, c))
        return self._go(back_to)

    def _error_character(self, c: str) -> int:
        line, col = self._where(self.pos)
        self.errors.append(LexicalError(_not_ascii(c, "source"), line, col, c))
        if self.trace:
            self._path.append("error")
            self._save_path(self.pos, c)
        self.pos += 1
        return END

    def _unterminated_string(self, start: int, message: str) -> int:
        line_end = self.src.find(NEWLINE, self.pos)
        if line_end == -1:
            line_end = self.n
        text = self.src[start:line_end]
        line, col = self._where(start)
        self.errors.append(LexicalError(message, line, col, text))
        if self.trace:
            self._path.append("error")
            self._save_path(start, text)
        self.pos = line_end
        return END

    def _restart_at_200(self, start: int) -> int:
        """No matching reserved-word transition -> restart at identifier state 200 from the first letter."""
        self.pos = start + 1                 # the first letter is the edge 0 --letter--> 200
        if self.trace:
            self._path.append("restart->200")
        return 200

    def _keyword_not_delimited(self, start: int, word: str, set_name: str, c: str) -> int:
        """A complete reserved word (e.g. "belial") is NOT followed by its delimiter.

        * c is a letter, digit or _  -> the word keeps going as an identifier
          (belial1, pass, prints, Trua2).
        * anything else (belial{)   -> lexical error, unless
          COMPLETE_KEYWORD_FALLS_BACK_TO_ID is True.
        """
        if c in alphanum_us or COMPLETE_KEYWORD_FALLS_BACK_TO_ID:
            return self._restart_at_200(start)
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
        if c == "g": return self._go(45)                  # g
        if c == "i": return self._go(54)                  # i
        if c == "I": return self._go(72)                  # I
        if c == "l": return self._go(79)                  # l
        if c == "n": return self._go(87)                  # n
        if c == "o": return self._go(92)                  # o
        if c == "p": return self._go(98)                  # p
        if c == "r": return self._go(115)                 # r
        if c == "s": return self._go(120)                 # s
        if c == "t": return self._go(127)                 # t
        if c == "T": return self._go(132)                 # T
        if c == "w": return self._go(137)                 # w
        # TD3: any other letter starts an identifier
        if c in letter: return self._go(200)
        # TD4: integer literals
        if c == "0": return self._go(241)
        if c in digit: return self._go(243)
        # TD2: reserved symbols (" and ' continue in TD5)
        if c == "+": return self._go(144)
        if c == "-": return self._go(148)                 # also TD4 (negative) and TD5 (--)
        if c == "*": return self._go(153)
        if c == "/": return self._go(157)                 # also TD5 (/--)
        if c == "%": return self._go(163)
        if c == "<": return self._go(167)
        if c == ">": return self._go(171)
        if c == "=": return self._go(175)
        if c == "!": return self._go(179)
        if c == "(": return self._go(182)
        if c == ")": return self._go(184)
        if c == "[": return self._go(186)
        if c == "]": return self._go(188)
        if c == "{": return self._go(190)
        if c == "}": return self._go(192)
        if c == ",": return self._go(194)
        if c == ":": return self._go(196)
        if c == ";": return self._go(198)
        if c == '"': return self._go(269)
        if c == "'": return self._go(272)
        # no edge from state 0
        if c == "_":
            return self._error(start, UNDERSCORE_START)
        return self._error(start, f"invalid character {_show(c)}")

    # ====================================== TD1  Reserved Words 1-136, 287-291
    def _td1_reserved_words(self, state: int, c: str, start: int) -> int:
        # Every final state is *: the delimiter is given back.
        # Trua (125-129) and Inaccu (65-71) produce the token type trua_lit.
        if state == 1:                                    # read "a"
            if c == "n": return self._go(2)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 2:                                    # read "an" (complete)
            if c in delim_logic: return self._accept(start, 3, "an")  # 2 -> 3*
            return self._keyword_not_delimited(start, "an", "delim_logic", c)
        if state == 4:                                    # read "b"
            if c == "e": return self._go(5)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 5:                                    # read "be"
            if c == "l": return self._go(6)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 6:                                    # read "bel"
            if c == "i": return self._go(7)
            if c == "s": return self._go(11)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 7:                                    # read "beli"
            if c == "a": return self._go(8)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 8:                                    # read "belia"
            if c == "l": return self._go(9)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 9:                                    # read "belial" (complete)
            if c in delim_io: return self._accept(start, 10, "belial")  # 9 -> 10*
            return self._keyword_not_delimited(start, "belial", "delim_io", c)  # keyword delimiter handling
        if state == 11:                                   # read "bels"
            if c == "a": return self._go(12)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 12:                                   # read "belsa" (complete)
            if c in delim_logic: return self._accept(start, 13, "belsa")  # 12 -> 13*
            return self._keyword_not_delimited(start, "belsa", "delim_logic", c)
        if state == 14:                                   # read "c"
            if c == "o": return self._go(15)
            if c == "y": return self._go(20)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 15:                                   # read "co"
            if c == "n": return self._go(16)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 16:                                   # read "con"
            if c == "s": return self._go(17)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 17:                                   # read "cons"
            if c == "t": return self._go(18)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 18:                                   # read "const" (complete)
            if c in delim_const: return self._accept(start, 19, "const")  # 18 -> 19*
            return self._keyword_not_delimited(start, "const", "delim_const", c)
        if state == 20:                                   # read "cy"
            if c == "c": return self._go(21)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 21:                                   # read "cyc"
            if c == "l": return self._go(22)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 22:                                   # read "cycl"
            if c == "a": return self._go(23)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 23:                                   # read "cycla" (complete)
            if c in delim_io: return self._accept(start, 24, "cycla")  # 23 -> 24*
            return self._keyword_not_delimited(start, "cycla", "delim_io", c)  # keyword delimiter handling
        if state == 25:                                   # read "d"
            if c == "e": return self._go(26)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 26:                                   # read "de"
            if c == "l": return self._go(27)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 27:                                   # read "del"
            if c == "e": return self._go(28)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 28:                                   # read "dele"
            if c == "o": return self._go(29)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 29:                                   # read "deleo" (complete)
            if c in delim_deleo: return self._accept(start, 30, "deleo")  # 29 -> 30*
            return self._keyword_not_delimited(start, "deleo", "delim_deleo", c)
        if state == 31:                                   # read "e"
            if c == "l": return self._go(32)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 32:                                   # read "el"
            if c == "s": return self._go(33)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 33:                                   # read "els"
            if c == "a": return self._go(34)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 34:                                   # read "elsa" (complete)
            if c in delim_block: return self._accept(start, 35, "elsa")  # 34 -> 35*
            return self._keyword_not_delimited(start, "elsa", "delim_block", c)  # keyword delimiter handling
        if state == 36:                                   # read "f"
            if c == "l": return self._go(42)
            if c == "o": return self._go(37)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 37:                                   # read "fo"
            if c == "r": return self._go(38)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 38:                                   # read "for"
            if c == "m": return self._go(39)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 39:                                   # read "form"
            if c == "o": return self._go(40)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 40:                                   # read "formo" (complete)
            if c in delim_io: return self._accept(start, 41, "formo")  # 40 -> 41*
            return self._keyword_not_delimited(start, "formo", "delim_io", c)
        if state == 42:                                   # read "fl"
            if c == "o": return self._go(43)
            return self._restart_at_200(start)
        if state == 43:                                   # read "flo" (complete)
            if c in delim_datatype: return self._accept(start, 44, "flo")
            return self._keyword_not_delimited(start, "flo", "delim_datatype", c)
        if state == 45:                                   # read "g"
            if c == "l": return self._go(46)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 46:                                   # read "gl"
            if c == "o": return self._go(47)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 47:                                   # read "glo"
            if c == "s": return self._go(48)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 48:                                   # read "glos"
            if c == "s": return self._go(49)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 49:                                   # read "gloss"
            if c == "a": return self._go(50)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 50:                                   # read "glossa"
            if c == "r": return self._go(51)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 51:                                   # read "glossar"
            if c == "e": return self._go(52)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 52:                                   # read "glossare" (complete)
            if c in delim_datatype: return self._accept(start, 53, "glossare")  # 52 -> 53*
            return self._keyword_not_delimited(start, "glossare", "delim_datatype", c)
        if state == 54:                                   # read "i"
            if c == "n": return self._go(55)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 55:                                   # read "in"
            if c == "n": return self._go(60)
            if c == "p": return self._go(64)
            if c == "s": return self._go(68)
            if c == "f": return self._go(56)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 56:                                   # read "inf"
            if c == "l": return self._go(57)
            return self._restart_at_200(start)
        if state == 57:                                   # read "infl"
            if c == "o": return self._go(58)
            return self._restart_at_200(start)
        if state == 58:                                   # read "inflo" (complete)
            if c in delim_io: return self._accept(start, 59, "inflo")
            return self._keyword_not_delimited(start, "inflo", "delim_io", c)
        if state == 60:                                   # read "inn"
            if c == "u": return self._go(61)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 61:                                   # read "innu"
            if c == "m": return self._go(62)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 62:                                   # read "innum" (complete)
            if c in delim_io: return self._accept(start, 63, "innum")  # 62 -> 63*
            return self._keyword_not_delimited(start, "innum", "delim_io", c)  # keyword delimiter handling
        if state == 64:                                   # read "inp"
            if c == "u": return self._go(65)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 65:                                   # read "inpu"
            if c == "b": return self._go(66)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 66:                                   # read "inpub" (complete)
            if c in delim_io: return self._accept(start, 67, "inpub")  # 66 -> 67*
            return self._keyword_not_delimited(start, "inpub", "delim_io", c)  # keyword delimiter handling
        if state == 68:                                   # read "ins"
            if c == "i": return self._go(69)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 69:                                   # read "insi"
            if c == "d": return self._go(70)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 70:                                   # read "insid" (complete)
            if c in INSID_DELIMITER: return self._accept(start, 71, "insid")  # 70 -> 71*
            return self._keyword_not_delimited(start, "insid", "INSID_DELIMITER", c)
        if state == 72:                                   # read "I"
            if c == "n": return self._go(73)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 73:                                   # read "In"
            if c == "a": return self._go(74)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 74:                                   # read "Ina"
            if c == "c": return self._go(75)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 75:                                   # read "Inac"
            if c == "c": return self._go(76)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 76:                                   # read "Inacc"
            if c == "u": return self._go(77)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 77:                                   # read "Inaccu" (complete)
            if c in delim_bool: return self._accept(start, 78, TRUA_LIT)  # 77 -> 78*
            return self._keyword_not_delimited(start, "Inaccu", "delim_bool", c)  # keyword delimiter handling
        if state == 79:                                   # read "l"
            if c == "i": return self._go(80)
            if c == "o": return self._go(83)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 80:                                   # read "li"
            if c == "s": return self._go(81)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 81:                                   # read "lis" (complete)
            if c in delim_datatype: return self._accept(start, 82, "lis")  # 81 -> 82*
            return self._keyword_not_delimited(start, "lis", "delim_datatype", c)  # keyword delimiter handling
        if state == 83:                                   # read "lo"
            if c == "o": return self._go(84)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 84:                                   # read "loo"
            if c == "d": return self._go(85)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 85:                                   # read "lood" (complete)
            if c in delim_io: return self._accept(start, 86, "lood")  # 85 -> 86*
            return self._keyword_not_delimited(start, "lood", "delim_io", c)  # keyword delimiter handling
        if state == 87:                                   # read "n"
            if c == "e": return self._go(88)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 88:                                   # read "ne"
            if c == "v": return self._go(89)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 89:                                   # read "nev"
            if c == "e": return self._go(90)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 90:                                   # read "neve" (complete)
            if c in delim_logic: return self._accept(start, 91, "neve")
            return self._keyword_not_delimited(start, "neve", "delim_logic", c)
        if state == 92:                                   # read "o"
            if c == "t": return self._go(93)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 93:                                   # read "ot"
            if c == "h": return self._go(94)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 94:                                   # read "oth"
            if c == "a": return self._go(95)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 95:                                   # read "otha"
            if c == "n": return self._go(96)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 96:                                   # read "othan" (complete)
            if c in delim_logic: return self._accept(start, 97, "othan")  # 96 -> 97*
            return self._keyword_not_delimited(start, "othan", "delim_logic", c)
        if state == 98:                                   # read "p"
            if c == "a": return self._go(99)
            if c == "e": return self._go(105)
            if c == "r": return self._go(111)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 99:                                   # read "pa"
            if c == "s": return self._go(100)
            if c == "u": return self._go(102)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 100:                                   # read "pas" (complete)
            if c in delim_stmt: return self._accept(start, 101, "pas")  # 100 -> 101*
            return self._keyword_not_delimited(start, "pas", "delim_stmt", c)  # keyword delimiter handling
        if state == 102:                                   # read "pau"
            if c == "s": return self._go(103)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 103:                                   # read "paus" (complete)
            if c in delim_stmt: return self._accept(start, 104, "paus")  # 103 -> 104*
            return self._keyword_not_delimited(start, "paus", "delim_stmt", c)  # keyword delimiter handling
        if state == 105:                                   # read "pe"
            if c == "r": return self._go(106)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 106:                                   # read "per"
            if c == "s": return self._go(107)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 107:                                  # read "pers"
            if c == "i": return self._go(108)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 108:                                  # read "persi"
            if c == "s": return self._go(109)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 109:                                  # read "persis" (complete)
            if c in delim_stmt: return self._accept(start, 110, "persis")  # 109 -> 110*
            return self._keyword_not_delimited(start, "persis", "delim_stmt", c)  # keyword delimiter handling
        if state == 111:                                  # read "pr"
            if c == "i": return self._go(112)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 112:                                  # read "pri"
            if c == "n": return self._go(113)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 113:                                  # read "prin" (complete)
            if c in delim_io: return self._accept(start, 114, "prin")  # 113 -> 114*
            return self._keyword_not_delimited(start, "prin", "delim_io", c)  # keyword delimiter handling
        if state == 115:                                  # read "r"
            if c == "e": return self._go(116)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 116:                                  # read "re"
            if c == "o": return self._go(117)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 117:                                  # read "reo"
            if c == "r": return self._go(118)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 118:                                  # read "reor" (complete)
            if c in REOR_DELIMITER: return self._accept(start, 119, "reor")  # 118 -> 119*
            return self._keyword_not_delimited(start, "reor", "REOR_DELIMITER", c)
        if state == 120:                                  # read "s"
            if c == "t": return self._go(121)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 121:                                  # read "st"
            if c == "r": return self._go(122)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 122:                                  # read "str"
            if c == "i": return self._go(123)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 123:                                  # read "stri"
            if c == "n": return self._go(124)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 124:                                  # read "strin"
            if c == "a": return self._go(125)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 125:                                  # read "strina" (complete)
            if c in delim_datatype: return self._accept(start, 126, "strina")  # 125 -> 126*
            return self._keyword_not_delimited(start, "strina", "delim_datatype", c)  # keyword delimiter handling
        if state == 127:                                  # read "t"
            if c == "r": return self._go(128)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 128:                                  # read "tr"
            if c == "u": return self._go(129)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 129:                                  # read "tru"
            if c == "a": return self._go(130)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 130:                                  # read "trua" (complete)
            if c in delim_datatype: return self._accept(start, 131, "trua")  # 130 -> 131*
            return self._keyword_not_delimited(start, "trua", "delim_datatype", c)  # keyword delimiter handling
        if state == 132:                                  # read "T"
            if c == "r": return self._go(133)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 133:                                  # read "Tr"
            if c == "u": return self._go(134)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 134:                                  # read "Tru"
            if c == "a": return self._go(135)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 135:                                  # read "Trua" (complete)
            if c in delim_bool: return self._accept(start, 136, TRUA_LIT)  # 135 -> 136*
            return self._keyword_not_delimited(start, "Trua", "delim_bool", c)  # keyword delimiter handling
        if state == 137:                                  # read "w"
            if c == "h": return self._go(138)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 138:                                  # read "wh"
            if c == "a": return self._go(139)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 139:                                  # read "wha"
            if c == "r": return self._go(140)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 140:                                  # read "whar"
            if c == "f": return self._go(141)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 141:                                  # read "wharf"
            if c == "a": return self._go(142)
            return self._restart_at_200(start)            # no reserved-word match
        if state == 142:                                  # read "wharfa" (complete)
            if c in delim_datatype: return self._accept(start, 143, "wharfa")  # 142 -> 143*
            return self._keyword_not_delimited(start, "wharfa", "delim_datatype", c)  # keyword delimiter handling
        raise AssertionError(f"unknown TD1 state {state}")

    # ============================================ TD2  Reserved Symbols 137-195
    def _td2_reserved_symbols(self, state: int, c: str, start: int) -> int:
        # Every final state is * except 154 (**).
        if state == 144:                                  # read "+"
            if c == "=":          return self._go(146)
            if c in delim_plus:   return self._accept(start, 145, "+")         # 144 -> 145*
            return self._error(start, _cannot_follow(c, "'+'", "delim_plus"))
        if state == 146:                                  # read "+="
            if c in delim_augoper: return self._accept(start, 147, "+=")        # 146 -> 147*
            return self._error(start, _cannot_follow(c, "'+='", "delim_augoper"))

        if state == 148:                                  # read "-"  (shared: TD2, TD5)
            if c == "=":                    return self._go(150)               # TD2: -=
            if c == "-":                    return self._go(275)               # TD5: -- comment
            if c in delim_oper:            return self._accept(start, 149, "-")   # 148 -> 149*
            return self._error(start, _cannot_follow(c, "'-'", "delim_oper"))
        if state == 150:                                  # read "-="
            if c in delim_augoper: return self._accept(start, 151, "-=")        # 150 -> 151*
            return self._error(start, _cannot_follow(c, "'-='", "delim_augoper"))

        if state == 153:                                  # read "*"
            if c == "=":          return self._go(155)
            if c in delim_arithmetic: return self._accept(start, 154, "*")         # 153 -> 154*
            return self._error(start, _cannot_follow(c, "'*'", "delim_arithmetic"))
        if state == 155:                                  # read "*="
            if c in delim_augoper: return self._accept(start, 156, "*=")        # 155 -> 156*
            return self._error(start, _cannot_follow(c, "'*='", "delim_augoper"))

        if state == 157:                                  # read "/"  (shared: TD2, TD5)
            if c == "=":          return self._go(159)
            if c == "-":          return self._go(161)
            if c in delim_arithmetic: return self._accept(start, 158, "/")         # 157 -> 158*
            return self._error(start, _cannot_follow(c, "'/'", "delim_oper"))
        if state == 159:                                  # read "/="
            if c in delim_augoper: return self._accept(start, 160, "/=")        # 159 -> 160*
            return self._error(start, _cannot_follow(c, "'/='", "delim_augoper"))
        if state == 161:                                  # read "/-"  (shared: TD2, TD5)
            if c == "-":          return self._go(277)                         # TD5: /-- comment
            # 154**: "/" then "-" then a delim_oper character (10/-2, a/-b).
            # Give back 2 characters ("-" and c), emit "/"; the "-" is read again.
            if c in delim_oper:  return self._accept(start, 162, "/", retract=2)
            return self._error(start, _cannot_follow(c, "'-'", "delim_oper"))

        if state == 163:                                  # read "%"
            if c == "=":          return self._go(165)
            if c in delim_arithmetic: return self._accept(start, 164, "%")         # 163 -> 164*
            return self._error(start, _cannot_follow(c, "'%'", "delim_arithmetic"))
        if state == 165:                                  # read "%="
            if c in delim_augoper: return self._accept(start, 166, "%=")        # 165 -> 166*
            return self._error(start, _cannot_follow(c, "'%='", "delim_augoper"))

        if state == 167:                                  # read "<"
            if c == "=":          return self._go(169)
            if c in delim_equality:  return self._accept(start, 168, "<")         # 167 -> 168*
            return self._error(start, _cannot_follow(c, "'<'", "delim_equality"))
        if state == 169:                                  # read "<="
            if c in delim_equality:  return self._accept(start, 170, "<=")        # 169 -> 170*
            return self._error(start, _cannot_follow(c, "'<='", "delim_equality"))

        if state == 171:                                  # read ">"
            if c == "=":          return self._go(173)
            if c in delim_equality:  return self._accept(start, 172, ">")         # 171 -> 172*
            return self._error(start, _cannot_follow(c, "'>'", "delim_equality"))
        if state == 173:                                  # read ">="
            if c in delim_equality:  return self._accept(start, 174, ">=")        # 173 -> 174*
            return self._error(start, _cannot_follow(c, "'>='", "delim_equality"))

        if state == 175:                                  # read "="
            if c == "=":          return self._go(177)
            if c in delim_equal:  return self._accept(start, 176, "=")         # 175 -> 176*
            return self._error(start, _cannot_follow(c, "'='", "delim_equal"))
        if state == 177:                                  # read "=="
            if c in delim_equality:  return self._accept(start, 178, "==")        # 177 -> 178*
            return self._error(start, _cannot_follow(c, "'=='", "delim_equality"))

        if state == 179:                                  # read "!"
            if c == "=":          return self._go(180)
            return self._error(start, f"'!' must be followed by '=' (found {_show(c)})")
        if state == 180:                                  # read "!="
            if c in delim_equality:  return self._accept(start, 181, "!=")        # 180 -> 181*
            return self._error(start, _cannot_follow(c, "'!='", "delim_equality"))

        if state == 182:                                  # read "("
            if c in delim_openparen: return self._accept(start, 183, "(")     # 182 -> 183*
            return self._error(start, _cannot_follow(c, "'('", "delim_openparen"))
        if state == 184:                                  # read ")"
            if c in delim_closeparen: return self._accept(start, 185, ")")     # 184 -> 185*
            return self._error(start, _cannot_follow(c, "')'", "delim_closeparen"))
        if state == 186:                                  # read "["
            if c in delim_openbracket: return self._accept(start, 187, "[")     # 186 -> 187*
            return self._error(start, _cannot_follow(c, "'['", "delim_openbracket"))
        if state == 188:                                  # read "]"
            if c in delim_closebracket: return self._accept(start, 189, "]")     # 188 -> 189*
            return self._error(start, _cannot_follow(c, "']'", "delim_closebracket"))
        if state == 190:                                  # read "{"
            if c in delim_opencurly: return self._accept(start, 191, "{")     # 190 -> 191*
            return self._error(start, _cannot_follow(c, "'{'", "delim_opencurly"))
        if state == 192:                                  # read "}"
            if c in delim_closecurly:     return self._accept(start, 193, "}")     # 192 -> 193*
            return self._error(start, _cannot_follow(c, "'}'", "delim_closecurly"))

        if state == 194:                                  # read ","
            if c in delim_comma:      return self._accept(start, 195, ",")     # 194 -> 195*
            return self._error(start, _cannot_follow(c, "','", "delim_comma"))
        if state == 196:                                  # read ":"
            if c in delim_colon:      return self._accept(start, 197, ":")     # 196 -> 197*
            return self._error(start, _cannot_follow(c, "':'", "delim_colon"))
        if state == 198:                                  # read ";"
            if c in delim_scolon:       return self._accept(start, 199, ";")     # 198 -> 199*
            return self._error(start, _cannot_follow(c, "';'", "delim_scolon"))

        # 269 and 272 (the opening quotes) are handled in _td5_strings_comments.
        # The quote states lead to string tokens through TD5, not quote tokens.
        # The quote-content sets define the characters accepted inside each string.
        # The TD5 states handle the closing quote and following delimiter, so those edges are
        # used directly; quotes are not emitted as separate tokens.
        raise AssertionError(f"unknown TD2 state {state}")

    # ================================================= TD3  Identifiers 196-235
    def _td3_identifiers(self, state: int, c: str, start: int) -> int:
        # identifier = letter (alphanum | _){0,19}: 1 to 20 characters.
        # States 200-218 cover characters 1-10; states 221-239 cover characters 11-20.
        if state == 200:                                  # 1 character
            if c in alphanum_us: return self._go(202)
            if c in ID_DELIMITER: return self._accept(start, 201, ID)  # 200 -> 201*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 202:                                  # 2 characters
            if c in alphanum_us: return self._go(204)
            if c in ID_DELIMITER: return self._accept(start, 203, ID)  # 202 -> 203*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 204:                                  # 3 characters
            if c in alphanum_us: return self._go(206)
            if c in ID_DELIMITER: return self._accept(start, 205, ID)  # 204 -> 205*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 206:                                  # 4 characters
            if c in alphanum_us: return self._go(208)
            if c in ID_DELIMITER: return self._accept(start, 207, ID)  # 206 -> 207*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 208:                                  # 5 characters
            if c in alphanum_us: return self._go(210)
            if c in ID_DELIMITER: return self._accept(start, 209, ID)  # 208 -> 209*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 210:                                  # 6 characters
            if c in alphanum_us: return self._go(212)
            if c in ID_DELIMITER: return self._accept(start, 211, ID)  # 210 -> 211*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 212:                                  # 7 characters
            if c in alphanum_us: return self._go(214)
            if c in ID_DELIMITER: return self._accept(start, 213, ID)  # 212 -> 213*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 214:                                  # 8 characters
            if c in alphanum_us: return self._go(216)
            if c in ID_DELIMITER: return self._accept(start, 215, ID)  # 214 -> 215*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 216:                                  # 9 characters
            if c in alphanum_us: return self._go(218)
            if c in ID_DELIMITER: return self._accept(start, 217, ID)  # 216 -> 217*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 218:                                  # 10 characters
            if c in alphanum_us: return self._go(221)
            if c in ID_DELIMITER: return self._accept(start, 219, ID)  # 218 -> 219*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 221:                                  # 11 characters
            if c in alphanum_us: return self._go(223)
            if c in ID_DELIMITER: return self._accept(start, 222, ID)  # 221 -> 222*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 223:                                  # 12 characters
            if c in alphanum_us: return self._go(225)
            if c in ID_DELIMITER: return self._accept(start, 224, ID)  # 223 -> 224*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 225:                                  # 13 characters
            if c in alphanum_us: return self._go(227)
            if c in ID_DELIMITER: return self._accept(start, 226, ID)  # 225 -> 226*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 227:                                  # 14 characters
            if c in alphanum_us: return self._go(229)
            if c in ID_DELIMITER: return self._accept(start, 228, ID)  # 227 -> 228*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 229:                                  # 15 characters
            if c in alphanum_us: return self._go(231)
            if c in ID_DELIMITER: return self._accept(start, 230, ID)  # 229 -> 230*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 231:                                  # 16 characters
            if c in alphanum_us: return self._go(233)
            if c in ID_DELIMITER: return self._accept(start, 232, ID)  # 231 -> 232*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 233:                                  # 17 characters
            if c in alphanum_us: return self._go(235)
            if c in ID_DELIMITER: return self._accept(start, 234, ID)  # 233 -> 234*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 235:                                  # 18 characters
            if c in alphanum_us: return self._go(237)
            if c in ID_DELIMITER: return self._accept(start, 236, ID)  # 235 -> 236*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 237:                                  # 19 characters
            if c in alphanum_us: return self._go(239)
            if c in ID_DELIMITER: return self._accept(start, 238, ID)  # 237 -> 238*
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        if state == 239:                                  # 20 characters (the maximum)
            if c in ID_DELIMITER: return self._accept(start, 240, ID)  # 239 -> 240*
            if c in alphanum_us: return self._overflow_error(start, ID_TOO_LONG)
            return self._error(start, _cannot_follow(c, "an identifier", "delim_id"))
        raise AssertionError(f"unknown TD3 state {state}")

    # ============================================ TD4  Integer and Float Literals 241-268 (+ supplemental 300)
    def _td4_integer_literals(self, state: int, c: str, start: int) -> int:
        # wharfa_lit: leading zeros do not count; then 1-8 significant digits.
        # ---- positive: 0 --0--> 241, 0 --digit--> 243 ----
        if state == 241:                                  # read "0", "00", ...  leading zeros do not count
            if c == "0":       return self._go(241)       # adj: keep leading zeros in the lexeme
            if c in digit:     return self._go(243)
            if c == ".":       return self._go(259)       # adj: decimal point starts a float
            if c in delim_num: return self._accept(start, 242, WHARFA_LIT)  # 241 -> 242*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_num"))
        if state == 243:                                  # 1 significant digit
            if c in numbers:   return self._go(245)
            if c == ".":       return self._go(259)       # adj: decimal point starts a float
            if c in delim_num: return self._accept(start, 244, WHARFA_LIT)  # 243 -> 244*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_num"))
        if state == 245:                                  # 2 significant digits
            if c in numbers:   return self._go(247)
            if c == ".":       return self._go(259)       # adj: decimal point starts a float
            if c in delim_num: return self._accept(start, 246, WHARFA_LIT)  # 245 -> 246*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_num"))
        if state == 247:                                  # 3 significant digits
            if c in numbers:   return self._go(249)
            if c == ".":       return self._go(259)       # adj: decimal point starts a float
            if c in delim_num: return self._accept(start, 248, WHARFA_LIT)  # 247 -> 248*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_num"))
        if state == 249:                                  # 4 significant digits
            if c in numbers:   return self._go(251)
            if c == ".":       return self._go(259)       # adj: decimal point starts a float
            if c in delim_num: return self._accept(start, 250, WHARFA_LIT)  # 249 -> 250*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_num"))
        if state == 251:                                  # 5 significant digits
            if c in numbers:   return self._go(253)
            if c == ".":       return self._go(259)       # adj: decimal point starts a float
            if c in delim_num: return self._accept(start, 252, WHARFA_LIT)  # 251 -> 252*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_num"))
        if state == 253:                                  # 6 significant digits
            if c in numbers:   return self._go(255)
            if c == ".":       return self._go(259)       # adj: decimal point starts a float
            if c in delim_num: return self._accept(start, 254, WHARFA_LIT)  # 253 -> 254*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_num"))
        if state == 255:                                  # 7 significant digits
            if c in numbers:   return self._go(257)
            if c == ".":       return self._go(259)       # adj: decimal point starts a float
            if c in delim_num: return self._accept(start, 256, WHARFA_LIT)  # 255 -> 256*
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_num"))
        if state == 257:                                  # 8 significant digits (the maximum)
            if c == ".":       return self._go(259)       # adj: decimal point is allowed after digit eight
            if c in delim_num: return self._accept(start, 258, WHARFA_LIT)  # 257 -> 258*
            if c in numbers:   return self._overflow_error(start, INT_TOO_LONG)
            return self._error(start, _cannot_follow(c, "a wharfa literal", "delim_num"))

        if state == 259:                                  # read the decimal point
            if c in numbers:   return self._go(261)
            if c in delim_num: return self._accept(start, 260, FLO_LIT)
            return self._error(start, _cannot_follow(c, "a flo literal", "delim_num"))
        if state == 261:                                  # 1 fraction digit
            if c in numbers:   return self._go(263)
            if c in delim_num: return self._accept(start, 262, FLO_LIT)
            return self._error(start, _cannot_follow(c, "a flo literal", "delim_num"))
        if state == 263:                                  # 2 fraction digits
            if c in numbers:   return self._go(265)
            if c in delim_num: return self._accept(start, 264, FLO_LIT)
            return self._error(start, _cannot_follow(c, "a flo literal", "delim_num"))
        if state == 265:                                  # 3 fraction digits
            if c in numbers:   return self._go(267)
            if c in delim_num: return self._accept(start, 266, FLO_LIT)
            return self._error(start, _cannot_follow(c, "a flo literal", "delim_num"))
        if state == 267:                                  # 4 fraction digits; read one more to round
            if c in delim_num: return self._accept(start, 268, FLO_LIT)
            if c in numbers:   return self._go(300)       # supplemental state records rounding lookahead
            return self._error(start, _cannot_follow(c, "a flo literal", "delim_num"))
        if state == 300:                                  # consume fractional digits beyond the diagram's four
            if c in numbers:   return self._go(300)
            if c in delim_num: return self._accept(start, 268, FLO_LIT)
            return self._error(start, _cannot_follow(c, "a flo literal", "delim_num"))
        raise AssertionError(f"unknown TD4 state {state}")

    # ================================= TD5  String Literals and Comments 269-281 (+ supplemental 301-302)
    def _td5_strings_comments(self, state: int, c: str, start: int) -> int:
        # ---- strina literal in double quotes: 0 --"--> 269 ----
        if state == 269:                                  # inside "..."
            if c == '"':          return self._go(270)    # closing quote
            if c == "\\":         return self._go(301)    # start of an escape
            if c in delim_dqopen - {'"', "\\"}: return self._go(269)  # loop
            if c in {NEWLINE, EOF}: return self._unterminated_string(start, STR_NO_CLOSE_DQ)
            return self._error_inside(269, _not_ascii(c, "a strina literal"), self.pos)
        if state == 301:                                  # read "\" inside "..."
            if "\\" + c in escape: return self._go(269)  # \" \' \\ \n \t \0
            if c == NEWLINE: return self._error_inside(269, _bad_escape(c), self.pos - 1)
            if c == EOF: return self._unterminated_string(start, STR_NO_CLOSE_DQ)
            return self._error_inside(269, _bad_escape(c), self.pos - 1)
        if state == 270:                                  # read the closing "
            if c in delim_dqclose or c == EOF: return self._accept(start, 271, STRINA_LIT)  # adj: eof may follow a closed string
            return self._error(start, _cannot_follow(c, "a strina literal", "delim_dqclose"))

        # ---- strina literal in single quotes: 0 --'--> 194 ----
        if state == 272:                                  # inside '...'
            if c == "'":          return self._go(273)    # closing quote
            if c == "\\":         return self._go(302)    # start of an escape
            if c in delim_sqopen - {"'", "\\"}: return self._go(272)  # loop
            if c in {NEWLINE, EOF}: return self._unterminated_string(start, STR_NO_CLOSE_SQ)
            return self._error_inside(272, _not_ascii(c, "a strina literal"), self.pos)
        if state == 302:                                  # read "\" inside '...'
            if "\\" + c in escape: return self._go(272)
            if c == NEWLINE: return self._error_inside(272, _bad_escape(c), self.pos - 1)
            if c == EOF: return self._unterminated_string(start, STR_NO_CLOSE_SQ)
            return self._error_inside(272, _bad_escape(c), self.pos - 1)
        if state == 273:                                  # read the closing '
            if c in delim_sqclose or c == EOF: return self._accept(start, 274, STRINA_LIT)  # adj: eof may follow a closed string
            return self._error(start, _cannot_follow(c, "a strina literal", "delim_sqclose"))

        # ---- single-line comment: 0 --'-'--> 141 --'-'--> 278 ----
        if state == 275:                                  # read "--"
            if c in {NEWLINE, EOF}:               return self._accept(start, 276, COMMENT_SL)   # 275 -> 276*
            if c in delim_slcomment: return self._go(275)
            if c == "/":                       return self._error(start, STRAY_CLOSER)
            return self._error_inside(275, _not_ascii(c, "a comment"), self.pos)
        # ---- multi-line comment: 0 --/--> 149 --'-'--> 153 --'-'--> 282 (comment transitions) ----
        if state == 277:                                  # inside "/-- ..."
            if c == "-":          return self._go(278)
            if c in delim_mlcomment_open: return self._go(277)  # loop
            if c == EOF:          return self._error(start, ML_UNTERMINATED)
            return self._error_inside(277, _not_ascii(c, "a comment"), self.pos)
        if state == 278:                                  # read "-" inside the comment
            if c == "-":          return self._go(279)
            if c in delim_mlcomment_open: return self._go(277)  # a lone "-" is comment text
            if c == EOF:          return self._error(start, ML_UNTERMINATED)
            return self._error_inside(277, _not_ascii(c, "a comment"), self.pos)
        if state == 279:                                  # read "--" inside the comment
            if c == "/":          return self._go(280)    # the first --/ closes the comment
            if c == "-":          return self._go(279)    # "---/" still closes
            if c in delim_mlcomment_open:   return self._go(277)    # "--x" is comment text
            if c == EOF:          return self._error(start, ML_UNTERMINATED)
            return self._error_inside(277, _not_ascii(c, "a comment"), self.pos)
        if state == 280:                                  # read the closing "--/"
            if c in delim_mlcomment_close: return self._accept(start, 281, COMMENT_ML)    # 280 -> 281*
            return self._error(start, _cannot_follow(c, "'--/'", "delim_mlcomment_close"))

        raise AssertionError(f"unknown TD5 state {state}")
