import asyncio
from unittest.mock import AsyncMock, MagicMock


def setup_llm_mock(agent):
    """Hàm chuyên dụng để mock tầng LLM Client thô"""
    agent.client._client = AsyncMock()

    # Tạo các chunk giả lập dữ liệu trả về từ LLM
    chunk1 = MagicMock()
    chunk1.choices = [
        MagicMock(finish_reason=None, delta=MagicMock(content="Xin chào! "))
    ]
    chunk1.usage = None

    chunk2 = MagicMock()
    chunk2.choices = [
        MagicMock(
            finish_reason="stop",
            delta=MagicMock(content="Đây là nội dung stream qua TUI."),
        )
    ]
    chunk2.usage = MagicMock(
        prompt_tokens=5,
        completion_tokens=10,
        total_tokens=15,
        prompt_tokens_details=MagicMock(cached_tokens=0),
    )

    async def fake_stream():
        yield chunk1
        await asyncio.sleep(0.2)  # Giả lập độ trễ mạng
        yield chunk2

    # Gắn luồng giả lập vào phương thức completions.create của client
    agent.client._client.chat.completions.create = AsyncMock(return_value=fake_stream())


from agent.events import AgentStreamEventType


async def run_agent_with_tui(agent, message: str, tui):
    """Hàm thực thi luồng agent và điều khiển hiển thị lên TUI"""
    assistance_streaming = False

    print(f"\n--- Bắt đầu xử lý tin nhắn: '{message}' ---")

    async for event in agent.run(message):
        # Bạn có thể in debug event ra nếu muốn kiểm chứng quá trình chuẩn hóa
        print(f"[DEBUG Event]: Type={event.type} | Data={event.data}")

        if event.type == AgentStreamEventType.TEXT_DELTA:
            content = event.data.get("content", "")
            if not assistance_streaming:
                tui.begin_assistance()
                assistance_streaming = True
            tui._stream_assistance_delta(content)

        elif event.type == AgentStreamEventType.TEXT_COMPLETE:
            if assistance_streaming:
                tui.end_assistance()
                assistance_streaming = False

        elif event.type == AgentStreamEventType.AGENT_ERROR:
            error = event.data.get("error", "Unknown error")
            print(f"\n[error]Error: {error}[/error]")

    print("\n--- Hoàn tất luồng xử lý ---")


import asyncio

# from agent.agent import Agent
# from tui.client import TUI
# from llm_mock import setup_llm_mock
# from agent_runner import run_agent_with_tui


async def main():
    # 1. Khởi tạo các thành phần
    agent = Agent()
    tui = TUI()

    # 2. Áp dụng Mock LLM vào agent
    setup_llm_mock(agent)

    # 3. Chạy agent và render qua TUI
    await run_agent_with_tui(agent, message="Hello, how are you?", tui=tui)


if __name__ == "__main__":
    asyncio.run(main())
