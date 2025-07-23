from essay_agent.utils.arg_resolver import ArgResolver

resolver = ArgResolver()

def test_alias_prompt_to_essay_prompt():
    planner_args = {"prompt": "This is the true essay prompt"}
    kwargs = resolver.resolve("brainstorm", planner_args=planner_args, context={}, user_input="", verbose=False)
    assert kwargs.get("essay_prompt") == "This is the true essay prompt" 