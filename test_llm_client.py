import asyncio
from unittest.mock import AsyncMock, MagicMock

from openai import RateLimitError
from client.llm_client import LLMClient
from client.response import StreamEventKind
from ui.tui import TUI, get_console


async def main():
    client = LLMClient()
    tui = TUI()

    client._client = AsyncMock()

    messages = [{"role": "user", "content": "Hello"}]

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
        await asyncio.sleep(2)  # Giả lập độ trễ mạng nhỏ giữa các chunk
        yield chunk2

    client._client.chat.completions.create = AsyncMock(return_value=fake_stream())

    # --- Bắt đầu luồng hiển thị lên TUI ---
    tui.begin_assistance()

    async for event in client.chat_completion(message=messages, stream=True):
        if event.type == StreamEventKind.TEXT_DELTA and event.text_delta:
            if event.text_delta.content:
                # Gọi phương thức stream delta của TUI
                tui._stream_assistance_delta(event.text_delta.content)
        elif event.type == StreamEventKind.TEXT_COMPLETE:
            # Có thể in thông tin usage nếu muốn (ví dụ in nhỏ bên dưới)
            if event.usage:
                tui.console.print(f"\n[dim]Token usage: {event.usage}[/dim]")

    tui.end_assistance()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].finish_reason = "stop"
    mock_response.choices[0].delta.content = "Test text delta"
    mock_response.usage = MagicMock(
        prompt_tokens=10,
        completion_tokens=14,
        total_tokens=20,
        prompt_tokens_details=MagicMock(cached_tokens=15),
    )

    client._client.chat.completions.create = AsyncMock(return_value=mock_response)

    # --- Bắt đầu luồng hiển thị lên TUI ---
    tui.begin_assistance()

    async for event in client.chat_completion(message=messages, stream=False):
        if event.type == StreamEventKind.TEXT_COMPLETE:
            if event.text_delta and event.text_delta.content:
                # Với non-stream, ta đổ toàn bộ content vào TUI delta
                tui._stream_assistance_delta(event.text_delta.content)

            if event.usage:
                tui.console.print(f"\n[dim]Token usage: {event.usage}[/dim]")
    tui.end_assistance()
    await client.close()

    # ==========================================
    # --- TEST TRƯỜNG HỢP GẶP LỖI (RateLimitError) ---
    # ==========================================
    tui.begin_assistance()
    tui.console.print(
        "\n[yellow]--- Đang test trường hợp lỗi (RateLimitError & Tự động Retry) ---[/yellow]"
    )

    # Tạo một response giả lập cho lỗi của OpenAI SDK
    mock_error_response = MagicMock()
    mock_error_response.status_code = 429

    # Dùng side_effect để ép hàm create() ném ra RateLimitError
    client._client.chat.completions.create = AsyncMock(
        side_effect=RateLimitError(
            message="Rate limit exceeded", response=mock_error_response, body=None
        )
    )

    # Gọi chat_completion và hứng sự kiện lỗi
    async for event in client.chat_completion(message=messages, stream=True):
        if event.type == StreamEventKind.ERROR:
            # In thông báo lỗi ra TUI hoặc console để kiểm chứng
            tui.console.print(f"\n[red]Bắt được lỗi chuẩn hóa: {event.error}[/red]")
            # Hoặc hiển thị qua TUI delta nếu muốn
            tui._stream_assistance_delta(f"\n[Lỗi]: {event.error}")

    tui.end_assistance()


if __name__ == "__main__":
    asyncio.run(main())
