from verifier.rules._shared import check_first_word


CONSTRAINT_ID = "GV-10"
PARAM_NAMES = ['word']


def check(response_text, params, context=None, meta=None):
    return check_first_word(CONSTRAINT_ID, response_text, params)
