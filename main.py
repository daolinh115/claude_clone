import asyncio
import sys
import click

from agent.agent import Agent
from agent.events import AgentStreamEventType
from ui.tui import TUI, get_console

console = get_console()


class CLI:
    def __init__(self):
        self.agent: Agent | None = None
        self.tui = TUI(console)

    async def run_single(self, message: str) -> str | None:
        async with Agent() as agent:
            self.agent = agent
            return await self._process_message(message)

    async def _process_message(self, message: str) -> str | None:
        if not self.agent:
            return None
        assistance_streaming = False
        final_response: str | None = None

        async for event in self.agent.run(message):
            if event.type == AgentStreamEventType.TEXT_DELTA:
                content = event.data.get("content", "")
                if not assistance_streaming:
                    self.tui.begin_assistance()
                    assistance_streaming = True
                self.tui._stream_assistance_delta(content)
            elif event.type == AgentStreamEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")
                if assistance_streaming:
                    self.tui.end_assistance()
                    assistance_streaming = False
            elif event.type == AgentStreamEventType.AGENT_ERROR:
                error = event.data.get("error", "Unknown error")
                console.print(f"\n[error]Error: {error}[/error]")

        return final_response


@click.command()
@click.argument("prompt", required=False)
def main(prompt: str | None):
    cli = CLI()
    # message = [{"role": "user", "content": prompt}]
    if prompt:
        result = asyncio.run(cli.run_single(prompt))
        if result is None:
            sys.exit(1)


if __name__ == "__main__":
    main()
