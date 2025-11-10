# MCP-Nodriver

[![smithery badge](https://smithery.ai/badge/@dragons96/mcp-undetected-chromedriver)](https://smithery.ai/server/@dragons96/mcp-undetected-chromedriver)

An MCP service built on nodriver, providing a comprehensive interface for automating Chrome browser control while bypassing anti-bot detection.

[中文文档](README_ZH.md)

> **Note:** The Chinese documentation and some Chinese comments in the code have been maintained through automatic translation during the migration from undetected-chromedriver to nodriver. I apologize for any translation inaccuracies - the alternative would have been to remove them completely, as I don't speak Chinese. Native Chinese speakers are welcome to submit corrections via pull requests.

## Installation


To install MCP-Nodriver for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@dragons96/mcp-undetected-chromedriver):

```bash
npx -y @smithery/cli install @dragons96/mcp-undetected-chromedriver --client claude
```

## Configuration to use Nodriver Server

Here's the Claude Desktop configuration to use the Nodriver server:

```json
{
  "mcpServers": {
    "mcp-nodriver": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@dragons96/mcp-undetected-chromedriver",
        "--config",
        "{}"
      ]
    }
  }
}
```


### Requirements

- Python >= 3.11
- Chrome browser

### Installation with uv

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# Linux/MacOS
source .venv/bin/activate

# Install dependencies
uv pip install -e .
```

> **Note for users in mainland China:** The PyPI mirror configuration for `https://pypi.tuna.tsinghua.edu.cn/simple` has been removed from the project configuration, as it should only be used by users in mainland China. If you need faster package downloads, you can configure it globally on your system:
>
> For pip:
> ```bash
> pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
> ```
>
> For uv, add the following to your global `~/.config/uv/uv.toml` (Linux/macOS) or `%APPDATA%\uv\uv.toml` (Windows):
> ```toml
> [[tool.uv.index]]
> url = "https://pypi.tuna.tsinghua.edu.cn/simple"
> default = true
> ```
>
> This approach allows you to configure the TUNA mirror based on your installation environment, so your Python installation will automatically prefer the faster proxy without affecting other users.

## Project Introduction

MCP-Nodriver is an MCP (Multi Channel Protocol) service that wraps the functionality of the nodriver library into a series of easy-to-use APIs. This project is particularly suitable for scenarios that require bypassing modern website anti-bot detection mechanisms in automated testing, data scraping, or web automation scripts.

### Key Features

- Based on nodriver, effectively bypassing website anti-bot detection
- Provides rich browser operation API interfaces
- Supports screenshots, PDF export, and other functionalities
- Supports complex page interaction operations such as clicking, form filling, dragging, etc.
- Seamlessly integrates with other tools in the MCP ecosystem

## Todo List

- [ ] Optimize browser driver management and handle driver interruptions
- [ ] Extend API capabilities
- [ ] Add more comprehensive error handling and logging
- [ ] Improve documentation with more usage examples
- [ ] Add support for browser profiles and extensions

## Usage

### Starting the Service

```bash
mcp-server-nodriver
```

### Available APIs

The service provides the following main API interfaces:

- `browser_navigate`: Navigate to a specified URL
- `browser_screenshot`: Take a screenshot of the current page
- `browser_click`: Click on page elements
- `browser_iframe_click`: Click on elements within an iframe
- `browser_fill`: Fill content in input fields
- `browser_select`: Select options in dropdown selection boxes
- `browser_hover`: Hover the mouse over elements
- `browser_evalute`: Execute JavaScript code
- `browser_close`: Close the browser
- `browser_get_visible_text`: Get visible text on the page
- `browser_get_visible_html`: Get visible HTML on the page
- `browser_go_back`: Navigate backward in browser history
- `browser_go_forward`: Navigate forward in browser history
- `browser_drag`: Drag elements
- `browser_press_key`: Simulate key presses
- `browser_save_as_pdf`: Save the page as a PDF

### Code Example

```python
from mcp.client import Client

# Create MCP client
client = Client()
client.start("nodriver-mcp-server")

# Navigate to website
response = client.call("browser_navigate", {"url": "https://example.com"})
print(response)

# Take a screenshot
response = client.call("browser_screenshot", {"name": "example"})
print(response)

# Get page text
response = client.call("browser_get_visible_text")
print(response.content[0].text)

# Close the browser
client.call("browser_close")
```

## How It Works

This service uses the nodriver library to create a specialized Chrome browser instance that effectively evades common anti-bot detection mechanisms. The service wraps these features through the MCP protocol, providing an easy-to-use API interface that makes automated testing and web scraping more convenient.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contribution Guidelines

Bug reports and feature requests are welcome on the GitHub Issues page. If you want to contribute code, please create an issue to discuss your ideas first.

## FAQ

**Q: Why choose nodriver instead of the standard selenium webdriver?**

A: nodriver is specifically designed to bypass anti-bot detection mechanisms of modern websites, such as Cloudflare, Distil Networks, etc., making it more reliable for data scraping and automated testing scenarios. It's a modern, async-first library that doesn't require chromedriver management.

**Q: How does the service handle browser instances?**

A: The service maintains a global browser instance, which is automatically created when an API requiring a browser is first called. The browser can be explicitly closed using the `browser_close` API.

**Q: How to handle elements within iframes?**

A: The `browser_iframe_click` API can directly operate on elements within iframes, without the need to manually switch frame contexts.
