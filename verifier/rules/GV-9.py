from verifier.rules._shared import check_forbidden_word


CONSTRAINT_ID = "GV-9"
PARAM_NAMES = ['forbidden_word']


def check(response_text, params, context=None, meta=None):
    return check_forbidden_word(CONSTRAINT_ID, response_text, params)
