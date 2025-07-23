import asyncio, json, os, logging

os.environ.setdefault("DEBUG_REASONING", "1")
os.environ.setdefault("ESSAY_AGENT_LOG_LEVEL", "DEBUG")

from essay_agent.agent_autonomous import AutonomousEssayAgent

async def main():
    agent = AutonomousEssayAgent("debug_user")
    user_msg = (
        "Brainstorm three unique challenge-focused story ideas about the time I struggled in calculus."
    )

    print("\n=== 1. OBSERVE ===")
    ctx = await agent._observe(user_msg)  # pylint: disable=protected-access
    print(json.dumps({k: type(v).__name__ for k, v in ctx.items()}, indent=2))

    print("\n=== 2. REASON ===")
    reasoning = await agent._reason(user_msg, ctx)  # pylint: disable=protected-access
    print(reasoning)

    print("\n=== 3. ACT ===")
    act_res = await agent._act(reasoning, user_msg)  # pylint: disable=protected-access
    print(act_res)

    print("\n=== 4. RESPOND ===")
    response = agent._respond(act_res, user_msg)  # pylint: disable=protected-access
    print(response)

if __name__ == "__main__":
    asyncio.run(main()) 