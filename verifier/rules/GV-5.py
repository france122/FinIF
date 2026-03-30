from verifier.rules._shared import check_numbered_list


CONSTRAINT_ID = "GV-5"
PARAM_NAMES = []


def check(response_text, params, context=None, meta=None):
    return check_numbered_list(CONSTRAINT_ID, response_text, params)
