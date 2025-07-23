import os, json
from essay_agent.cli import main
from essay_agent.memory.smart_memory import SmartMemory

def test_cli_persist_prompt(tmp_path, monkeypatch):
    user="persist_user"
    argv=["write","-p","My Prompt","--college","Stanford","--user",user,"--steps","brainstorm","--allow-demo"]
    monkeypatch.chdir(tmp_path)
    # run CLI; offline stub
    os.environ["ESSAY_AGENT_OFFLINE_TEST"]="1"
    main(argv)
    mem=SmartMemory(user)
    assert mem.get("essay_prompt","")=="My Prompt"
    assert mem.get("college","")=="Stanford" 