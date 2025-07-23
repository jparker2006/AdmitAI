from essay_agent.utils.arg_resolver import ArgResolver, MissingRequiredArgError
from essay_agent.tools import get_required_args

resolver = ArgResolver()

def test_brainstorm_resolve():
    context = {
        "essay_prompt": "Describe a challenge you faced",
        "user_profile": {},
    }
    kwargs = resolver.resolve(
        "brainstorm", planner_args={}, context=context, user_input="help"
    )
    for arg in get_required_args("brainstorm"):
        assert arg in kwargs


def test_missing_required():
    context = {}
    try:
        resolver.resolve("brainstorm", planner_args={}, context=context, user_input="")
    except MissingRequiredArgError:
        assert True
    else:
        assert False, "Expected MissingRequiredArgError" 