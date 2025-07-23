import os

os.environ["ESSAY_AGENT_OFFLINE_TEST"] = "1"


def test_psutil_import_stub():
    import psutil  # noqa: F401 – should succeed with stub

    assert hasattr(psutil, "cpu_percent")


def test_legacy_proxy_imports():
    import essay_agent.conversation as conv  # noqa: F401
    import essay_agent.planner as planner  # noqa: F401
    import essay_agent.planning as planning  # noqa: F401

    assert hasattr(planner, "EssayPlan") 