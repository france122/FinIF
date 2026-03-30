from verifier.rules._shared import check_currency_rule


CONSTRAINT_ID = "FV-5"
PARAM_NAMES = ['currency_rule']


def check(response_text, params, context=None, meta=None):
    return check_currency_rule(CONSTRAINT_ID, response_text, params)
