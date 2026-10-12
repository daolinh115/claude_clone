from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from utils.paths import is_binary_file, resolve_path
from utils.text import count_tokens, truncate_text


class ReadfileParams(BaseModel):
    path: str = Field(
        ...,
        description="Path to file to read (relative to working directory or absolute)",
    )
    offset: int = Field(
        1, ge=1, description="Line number to start reading from (1-base). Default to 1"
    )
    limit: int = Field(
        None,
        ge=1,
        description="Maximum number of line to read. If not specify enter reads entire file",
    )


class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "Read the contents of a text file. Returns the file content with line numbers. "
        "For large files, use offset and limit to read specific portions. "
        "Cannot read binary files (images, executables, etc.)."
    )
    kind = ToolKind.READ
    schema = ReadfileParams
    MAX_FILE_SIZE = 1024 * 1024 * 10
    MAX_OUTPUT_TOKENS = 25000

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ReadfileParams(**invocation.params)
        path = resolve_path(invocation.cwd, params.path)
        if not path.exists():
            return ToolResult.error(f"File not found {path}")
        if not path.is_file():
            return ToolResult.error(f"Path is not a file {path}")
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            return ToolResult.error(
                f"File too large ({file_size/(1024*1024):.1f}MB)."
                f"Maximum is {self.MAX_FILE_SIZE/(1024*1024):.0f}MB"
            )
        if is_binary_file(path):
            file_size_mb = file_size / (1024 * 1024)
            size_str = (
                f"{file_size_mb:.2f}MB" if file_size_mb >= 1 else f"{file_size} bytes"
            )
            return ToolResult.error_result(
                f"Cannot read binary file: {path.name} ({size_str}) "
                f"This tool only reads text files."
            )
        try:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = path.read_text(encoding="latin-1")
            lines = content.splitlines()
            total_lines = len(lines)
            if total_lines == 0:
                return ToolResult.success_result("File is empty.", metadata={"line": 0})

            start_idx = max(0, params.offset - 1)
            if params.limit is not None:
                end_idx = min(start_idx + params.limit, total_lines)
            else:
                end_idx = total_lines
            selected_line = lines[start_idx:end_idx]
            formatted_lines = []
            for i, line in enumerate(selected_line, start_idx + 1):
                formatted_lines.append(f"{i:6}|{line}")
            output = "\n".join(formatted_lines)
            token_count = count_tokens(output)
            if token_count > self.MAX_OUTPUT_TOKENS:
                output = truncate_text(
                    output,
                    self.MAX_OUTPUT_TOKENS,
                    suffix=f"\n... [truncate {total_lines} total lines] ",
                )
                truncated = True
            metadata_lines = []
            if start_idx > 0 or end_idx < total_lines:
                metadata_lines.append(
                    f"showing lines {start_idx + 1}-{end_idx} of {total_lines}"
                )
            if metadata_lines:
                header = " | ".join(metadata_lines) + "\n\n"
                output = header + output
            return ToolResult.success_result(
                output=output,
                truncated=truncated,
                metadata={
                    "path": str(path),
                    "total_lines": total_lines,
                    "shown_start": start_idx + 1,
                    "shown_end": end_idx,
                },
            )
        except Exception as e:
            ToolResult.error_result(f"Failed to read file: {e}")
