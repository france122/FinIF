from verifier.rules._shared import check_markdown_table


CONSTRAINT_ID = "GV-6"
PARAM_NAMES = []


def check(response_text, params, context=None, meta=None):
    return check_markdown_table(CONSTRAINT_ID, response_text, params)
