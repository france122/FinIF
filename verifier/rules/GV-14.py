from verifier.rules._shared import check_bullet_prefix


CONSTRAINT_ID = "GV-14"
PARAM_NAMES = ['prefix']


def check(response_text, params, context=None, meta=None):
    return check_bullet_prefix(CONSTRAINT_ID, response_text, params)
