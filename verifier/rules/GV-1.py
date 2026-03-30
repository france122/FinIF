from verifier.rules._shared import check_max_chars


CONSTRAINT_ID = "GV-1"
PARAM_NAMES = ['n']


def check(response_text, params, context=None, meta=None):
    return check_max_chars(CONSTRAINT_ID, response_text, params)
