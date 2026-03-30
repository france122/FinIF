from verifier.rules._shared import check_conditional_followup


CONSTRAINT_ID = "FV-3"
PARAM_NAMES = ['trigger', 'followup']


def check(response_text, params, context=None, meta=None):
    return check_conditional_followup(CONSTRAINT_ID, response_text, params)
