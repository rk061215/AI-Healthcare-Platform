from loguru import logger


class AgentOrchestrator:
    def __init__(self):
        self.agents = {}

    def register_agent(self, name: str, agent) -> None:
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")

    async def run(self, agent_name: str, state: dict) -> dict:
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        logger.info(f"Running agent: {agent_name}")
        return await self.agents[agent_name].ainvoke(state)
