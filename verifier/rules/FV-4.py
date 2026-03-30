from verifier.rules._shared import check_descending_order


CONSTRAINT_ID = "FV-4"
PARAM_NAMES = ['order_field']


def check(response_text, params, context=None, meta=None):
    return check_descending_order(CONSTRAINT_ID, response_text, params)
