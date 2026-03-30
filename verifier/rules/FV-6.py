from verifier.rules._shared import check_risk_level


CONSTRAINT_ID = "FV-6"
PARAM_NAMES = []


def check(response_text, params, context=None, meta=None):
    return check_risk_level(CONSTRAINT_ID, response_text, params)
