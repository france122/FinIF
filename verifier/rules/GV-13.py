from verifier.rules._shared import check_first_last_line


CONSTRAINT_ID = "GV-13"
PARAM_NAMES = ['first_line', 'last_line']


def check(response_text, params, context=None, meta=None):
    return check_first_last_line(CONSTRAINT_ID, response_text, params)
