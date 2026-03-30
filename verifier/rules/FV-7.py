from verifier.rules._shared import check_rating_word


CONSTRAINT_ID = "FV-7"
PARAM_NAMES = []


def check(response_text, params, context=None, meta=None):
    return check_rating_word(CONSTRAINT_ID, response_text, params)
