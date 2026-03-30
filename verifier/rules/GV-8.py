from verifier.rules._shared import check_keywords_exist


CONSTRAINT_ID = "GV-8"
PARAM_NAMES = ['kw1', 'kw2']


def check(response_text, params, context=None, meta=None):
    return check_keywords_exist(CONSTRAINT_ID, response_text, params)
