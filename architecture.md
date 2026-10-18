# 🗺️ Architecture Map (Claude Clone)

## project
```text
├── main.py				      # Entry point (Nhận prompt từ user -> Khởi tạo agent -> Hiện thị kết quả lên terminal)

├── agent/					   # Tầng điều phối
│   ├── agent.py			   # Điều phối toàn bộ vòng đời của Agent (Nó kết nối: ContextManager + LLMClient + ToolRegistry)
│   └── events.py			   # Data contract giữa Agent vs UI (Agent không trả string, Agent phát event)

├── client/				      # Đây là tầng giao tiếp với LLM
│   ├── llm\_client.py	   # Giao tiếp OpenRouter/OpenAI (OpenRouter API, Retry, Streaming, Response Parsing)
│   └── response.py		   # Data contract giữa LLM vs Agent

├── context/
│   └── manager.py		   # Quản lý hội thoại (System prompt, User Message và Assistant Message)
├── tools/
│   ├── base.py			   # Framework cho Tool (định nghĩa tool là gì? toolresult là gì? toolInvocation là gì)
│   ├── registry.py		   # Quản lý Tool Registry (Đăng ký tool, tìm tool, Invoke tool, Xuất OpenAI Schema)
│   └── builtin/
│       └── read\_file.py	# Công cụ đọc file
├── prompt/
│   └── system.py			   # System Prompt
├── ui/
│   └── tui.py				   # Terminal UI (In output đẹp ra terminal)
└── utils/					   # Các helper dùng chung
   ├── text.py			      # Token utilities (Đếm token, cắt text theo token)
   └── paths.py			   # File path utilities (Resolve path, check binary file)

```
----------------------------------------------------------------------------------------


# main.py
## Trách nhiệm:

1. Nhận prompt từ CLI
2. Khởi tạo Agent
3. Nhận AgentEvent từ Agent
4. Chuyển AgentEvent thành giao diện hiển thị (TUI)
5. Kết thúc chương trình

# Input
1. Prompt nhận được từ CLI
2. event nhận được từ Agent

## Trigger
Khi user chạy từ CLI
## Process
bước 1: Khởi tạo CLI
bước 2: Tạo Agent
bước 3: Truyền message cho Agent
bước 4: Lằng nghe AgentEvent
bước 5: Xử lý Text_Delta
bước 6: Xử lý Text_Complete
bước 7: Xử lý error
bước 8: Trả kết quả cuối

## Error Handling
Trường hợp 1: Agent chưa tồn tại
Trường hợp 2: Agent phát lỗi
Trườn hợp 3: Không có response

## Output
Output cho user

----------------------------------------------------------

# agent.py

## Trách Nhiệm
1. Nhận message từ UI
2. Lưu message vào Context
3. Gọi LLM
4. Chuyển StreamEvent thành AgentEvent
5. Lưu câu trả lời vào Context
6. Trả AgentEvent cho UI

## Trigger
1. Ai gọi file này: main gọi async with Agent() as agent:
2. Khi nào được kích hoạt

## Input
1. User message
2. Conversation context
3. Tool Schema

## Process
bước 1: Khởi tạo Agent (1 llm, 1 context và 1 registry)
bước 2: Bắt đầu xử lý request, agent phát event thông báo: "tôi bắt đầu xử lý"	
bước 3: Lưu user message vào context manager
bước 4: Chạy agent loop (đây là phần giao tiếp với LLM)
bước 5: Chuẩn hóa dữ liệu trả về từ llm
bước 6: Tích luỹ toàn bộ response (response += content)
bước 7: Sau khi stream kết thúc, lưu vào assistant Message
bước 8: Phát Text\_Complete
bước 9: Phát thông báo Agent hoàn thành công việc

## Error Handling
Trường hợp 1: LLM lỗi
Trường hợp 2: Client đóng kết nối

## Output
Agent phát AgentEvent
---------------------------------------------------------------------

# llm\_client.py
## Trách Nhiệm
1. Tạo kết nối tới OpenRouter
2. Gửi chat completion request
3. Quản lý retry khi API lỗi
4. Xử lý stream/non-stream response
5. Chuẩn hóa response thành StreamEvent
6. Đóng kết nối khi không còn sử dụng

## Trigger
1. Ai gọi file này: agent gọi trong agent.\_agentic\_loop()
2. Khi nào được kích hoạt: Sau khi context chuẩn bị xong message, agent gọi chat\_completion(...)

## Input
1. message: Nguồn ContexManager.get\_messages()
2. tools: Nguồn ToolRegistry.get\_schemas()
3. Stream
4. Environment Variable đọc từ OPENROUTER\_API\_KEY

### Process
bước 1: Lấy hoặc tạo API client thông quat get\_client()
bước 2: Chuẩn bị request (tạo tham số kwargs)
bước 3: Gửi request client.chat.completions.create(...)
bước 4: Chọn chế độ stream or non\_stream
bước 5: Chuẩn hoá dữ liệu
bước 6: Trả event

## Error Handling
1. RateLimitError
2. APIConnectionError
3. APIError

## Output
AsyncGenerator\[StreamEvent]

--------------------------------------------------

# manager.py

## Trách Nhiệm
Là nơi lưu trữ system prompt, user message và assistant message và chuyển chúng thành định dạng mà LLM có thể hiểu được

## Trigger
Nó được gọi trong agent.py
1. Khi user gửi cấu hỏi: context\_manager.add\_user\_message(...)
2. Khi LLM trả lời xong: context\_manager.add\_assistant\_message()
3. Khi Agent chuẩn bị gọi LLM: context\_manager.get\_message()

## Input
1. system prompt
2. User message
3. Assistant message
4. model\name: Dùng để đếm token cho từng message

## Process
Bước 1: Khởi tạo context
Bước 2: Lưu User Message
Bước 3: Lưu Assitant Message
Bước 4: Build messages cho LLM

## Error Handling
Don't have

## Output
1. Sau khi gọi, add\_user\_message(...) vs add\_assistant\_message(...) thì output là cập nhật state nội bộ.
2. Gọi get\_messages() thì output: list\[dict\[str,Any]]

-----------------------------------------------------------------------

# base.py

## Trách Nhiệm
Nó trả lời các câu hỏi:
1. Tool là gì?
2. Kết quả Tool là gì?
3. Tool được gọi như thế nào?
4. Tool nhận tham số gì?
5. Tool nào cần xác nhận trước khi chạy?
6. Tool schema được tạo ra như thế nào?

## Trigger
1. Ai gọi file này: Hầu hết các file trong module tools
2. Khi nào được kích hoạt:
   - Khi đăng ký tool: registry.register(tool)
   - Khi validate tham số tool: tool.validate\_params
   - Khi gọi tool: tool.execute()
   - Khi xuất OpenAI Schema



## Input
1. Tool parameters
2. ToolInvocation
3. Pydantic Model

## Process
Thành phần 1: ToolKind (địng nghĩa các loại tool)
Thành phần 2: ToolResult (định nghĩa kết quả chuẩn của mọi loại tool, data contract giữa tool và registry)
Thành phần 3: ToolInvocation: Chứa thông tin mỗi lần gọi tool.
Thành phần 4: ToolConfirmation: Mô tả yêu cầu xác nhận trước khi chạy Tool nguy hiểm.
Thành phần 5: Abstract Tool: Nó định nghĩa interface chuẩn mà mọi Tool bắt buộc phải có.
Thành phần 6: Validate Parameters: Kiểm tra tham số đầu vào có hợp lệ không.
Thành phần 7: Kiểm tra Mutating tool: Xác định tool có làm thay đổi hệ thống không
Thành phần 8: OpenAI Schema Generation: Cầu nói giữa Tool Framework vs LLM Function Calling

## Error Handling
No

## Output
Không trả Output cho user

-----------------------------------------------------------------------

# Registry.py

## Trách Nhiệm
Quản lý toàn bộ tool trong hệ thống:
1. Tool nào đang tồn tại?
2. Tool nào được đăng ký?
3. Tool nào cần được gọi?
4. Tool nào cần xuất schema cho LLM?

### Trigger
1. Ai gọi file này: Thông qua self.tool\_registry = create\_default\_registry() vs self.tool\_registry.get\_schemas()
2. Khi nào được kích hoạt: 
   - Khi Agent khởi tạo: Agent()->create\_default\_registry()->ToolRegistry()->register(...)
   - Khi cần gửi Tool Schema cho LLM: tool\_registry.get\_schemas()
   - Trong tương lai: Agent sẽ gọi: tool\_registry.invoke(...)

## Input
1. Tool object khi đăng ký tool: create\_default\_registry()
2. Tool name
3. Tool parameters
4. Working Directory

## Process
Bước 1: Khởi tạo Registry
Bước 2: Đăng ký Tool (register(tool))
Bước 3: Tìm tool
Bước 4: Lấy danh sách Tool
Bước 5: Xuất Tool Schema
Bước 6: Gọi Tool invoke: 
   - Tìm tool (tool = self.get(name))
   - Validate Parameter: tool.validate\_params
   - Tạo ToolInvocation
   - tool.execute(...)
   - ToolResult

## Error Handling
Trường hợp 1: Tool không tồn tại
Trường hợp 2: Parameter sai
Trường hợp 3: Tool execute lỗi

## Output
1. Danh sách Tool.
2. Danh sách Schema.
3. Tạo Object
4. ToolResult

-----------------------------------------------------------------------

# .py

## Trách Nhiệm

## Trigger

## Input

## Process

## Error Handling

## Output

































