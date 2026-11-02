import asyncio
from pathlib import Path
from tools.registry import (
    ToolRegistry,
    create_default_registry,
)  # Điều chỉnh import tùy theo cấu trúc thư mục thực tế của bạn


async def main():
    print("Đang khởi tạo ToolRegistry...")
    registry = create_default_registry()

    # In ra danh sách các tool đã đăng ký
    tools = registry.get_tools()
    print(f"Đã đăng ký thành công {len(tools)} tool:")
    for t in tools:
        print(f" - {t.name}: {t.description}")

    # Thử lấy schema gửi cho LLM
    schemas = registry.get_schemas()
    print(f"Lấy thành công {len(schemas)} schemas.")


if __name__ == "__main__":
    asyncio.run(main())
