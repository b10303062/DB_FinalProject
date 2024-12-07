STYLE_DEFAULT = "\033[0m"
STYLE_BOLD = "\033[1m"
FG_COLOR_RED = "\033[91m"
FG_COLOR_GREEN = "\033[92m"
FG_COLOR_YELLOW = "\033[38;5;226m"
RESET_BUFFER = "\033c"
SET_CURSOR_TO_LEFT_TOP = "\033[H"
ERASE_DISPLAY = "\033[J"
SAVE_CURSOR_AND_USE_ALTERNATE = "\033[?1049h"
RESTORE_CURSOR_AND_USE_NORMAL = "\033[?1049l"

PRESS_ENTER_TO_CONTINUE = "{}Press ENTER to continue ...{}".format(STYLE_BOLD, STYLE_DEFAULT)

PROMPT = "{}>{} ".format(STYLE_BOLD, STYLE_DEFAULT)

def clear_screen():
    print(RESET_BUFFER, flush = True, end = "")

def to_alternate_screen():
    print(SAVE_CURSOR_AND_USE_ALTERNATE, flush = True, end = "")

def to_normal_screen():
    print(RESTORE_CURSOR_AND_USE_NORMAL, flush = True, end = "")

def command_prompt(username = ""):
    print("\n{} {}".format(username, PROMPT), end = "")

def press_enter_to_continue():
    print('\n' + PRESS_ENTER_TO_CONTINUE)
    _ = input()

def bold_text(text: str) -> str:
    return STYLE_BOLD + text + STYLE_DEFAULT

def red_text(text: str) -> str:
    return FG_COLOR_RED + text + STYLE_DEFAULT

def green_text(text: str) -> str:
    return FG_COLOR_GREEN + text + STYLE_DEFAULT