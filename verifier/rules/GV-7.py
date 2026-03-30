from verifier.rules._shared import check_json_format


CONSTRAINT_ID = "GV-7"
PARAM_NAMES = []


def check(response_text, params, context=None, meta=None):
    return check_json_format(CONSTRAINT_ID, response_text, params)
