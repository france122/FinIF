from verifier.rules._shared import check_last_line_equals


CONSTRAINT_ID = "FV-1"
PARAM_NAMES = ['risk_line']


def check(response_text, params, context=None, meta=None):
    return check_last_line_equals(CONSTRAINT_ID, response_text, params)
