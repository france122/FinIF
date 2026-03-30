from verifier.rules._shared import check_contains_phrase


CONSTRAINT_ID = "FV-2"
PARAM_NAMES = ['disclaimer']


def check(response_text, params, context=None, meta=None):
    return check_contains_phrase(CONSTRAINT_ID, response_text, params)
