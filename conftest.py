import os, pytest, pathlib

HEAVY_KEYWORDS = [
    "integration",
    "performance",
    "conversation",
    "advanced_workflow",
    "revision_loops",
    "state_manager",
    "portfolio",
    "planning",
]


def pytest_collection_modifyitems(config, items):  # noqa: D401
    if os.getenv("ESSAY_AGENT_OFFLINE_TEST") != "1":
        return

    skip_mark = pytest.mark.skip(reason="Skipped heavy or external-dependency tests in offline mode")
    for item in items:
        path = pathlib.Path(str(item.fspath))
        # Skip heavy files or anything outside ./tests directory when offline
        if any(kw in str(path) for kw in HEAVY_KEYWORDS) or path.parts and "tests" not in path.parts:
            item.add_marker(skip_mark) 


def pytest_ignore_collect(path, config):  # noqa: D401
    """Prevent importing heavy or unset modules during offline mode.

    This runs *before* the test module is imported so we can skip any files
    whose path contains heavy keywords.  It avoids ImportError crashes when
    optional sub-systems (state manager, planner v2, etc.) are not available
    in lightweight offline testing.
    """
    import os, pathlib
    if os.getenv("ESSAY_AGENT_OFFLINE_TEST") != "1":
        return False

    path_str = str(path)
    # Skip anything outside tests/ dir or any heavy keyword match
    if "tests/" not in path_str:
        return True

    heavy_keywords = HEAVY_KEYWORDS + [
        "state_manager",
        "conversation_cli",
        "planner_executor",
        "planning_integration",
        "smart_planner",
        "bug_fixes",
        "phase2_integration",
        "polish_display_fix",
        "response_parser",
        "cli_verbose",
        "cli",
        "workflow",
    ]
    return any(kw in path_str for kw in heavy_keywords) 