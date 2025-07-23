"""Legacy proxy module for backward-compatibility in unit tests.

Re-exports public symbols from essay_agent.agents.communication.
This proxy is *not* used by the main code-base and will be removed in Phase-5.
"""

from essay_agent.agents.communication import *  # type: ignore # pylint: disable=wildcard-import,unused-wildcard-import 