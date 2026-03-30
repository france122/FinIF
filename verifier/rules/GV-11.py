from verifier.rules._shared import check_checkbox


CONSTRAINT_ID = "GV-11"
PARAM_NAMES = []


def check(response_text, params, context=None, meta=None):
    return check_checkbox(CONSTRAINT_ID, response_text, params)
