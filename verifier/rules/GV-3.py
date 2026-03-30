from verifier.rules._shared import check_paragraphs


CONSTRAINT_ID = "GV-3"
PARAM_NAMES = ['n']


def check(response_text, params, context=None, meta=None):
    return check_paragraphs(CONSTRAINT_ID, response_text, params)
