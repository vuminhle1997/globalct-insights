from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.llms import LLM
from llama_index.core.tools import BaseTool


def create_agent(system_prompt: str, tools: list[BaseTool], llm: LLM, **kwargs) -> ReActAgent:
    """
    Creates and configures a ReActAgent with specified parameters.

    Args:
        system_prompt (str): System prompt template for the agent
        tools (List[BaseTool]): List of tools available to the agent
        llm (LLM): LLM
        **kwargs: Additional keyword arguments to pass to ReActAgent

    Returns:
        ReActAgent: Configured agent instance with updated prompts and specified parameters

    Example:
        >>> system_prompt = "You are a helpful assistant"
        >>> tools = [Tool1(), Tool2()]
        >>> agent = create_agent(system_prompt, tools, llm)
    """
    agent = ReActAgent(
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        **kwargs,
    )
    return agent
