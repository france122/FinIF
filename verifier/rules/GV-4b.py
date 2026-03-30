from verifier.rules._shared import check_heading_levels


CONSTRAINT_ID = "GV-4b"
PARAM_NAMES = ['n']


def check(response_text, params, context=None, meta=None):
    return check_heading_levels(CONSTRAINT_ID, response_text, params)
