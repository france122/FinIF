from verifier.rules._shared import check_markdown_format


CONSTRAINT_ID = "GV-4a"
PARAM_NAMES = []


def check(response_text, params, context=None, meta=None):
    return check_markdown_format(CONSTRAINT_ID, response_text, params)
