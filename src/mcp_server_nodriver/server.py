import base64
import datetime
import os
import asyncio
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP
from mcp import types
from mcp.types import TextContent
from typing import Callable, Coroutine, Any
import nodriver as uc


class Global:
    browser = None


async def reset_browser_state():
    if Global.browser:
        await Global.browser.stop()
        Global.browser = None


async def ensure_browser(config: dict | None = None):
    if not Global.browser:
        Global.browser = await uc.start()
    return Global.browser


async def create_success_response(message: str | list[str]) -> types.CallToolResult:
    if isinstance(message, str):
        message = [message]
    return types.CallToolResult(
        content=[TextContent(type="text", text=msg) for msg in message],
        isError=False,
    )


async def create_error_response(message: str) -> types.CallToolResult:
    return types.CallToolResult(
        content=[TextContent(type="text", text=message)],
        isError=True,
    )


@dataclass
class ToolContext:
    browser: uc.Browser | None = None


class Tool:

    async def safe_execute(
            self,
            context: ToolContext,
            handler: Callable[[uc.Browser], Coroutine[Any, Any, types.CallToolResult]],
    ) -> types.CallToolResult:
        try:
            return await handler(context.browser)
        except AssertionError as error:
            return await create_error_response(f"Params error: {str(error)}")
        except Exception as error:
            return await create_error_response(f"Operation failed: {str(error)}")


tool = Tool()


mcp = FastMCP(
    "nodriver-mcp-server",
)


@mcp.tool()
async def browser_navigate(url: str, timeout: int = 30000):
    """Navigate to a URL

    Args:
        url: The URL to navigate to - required
        timeout: The timeout for the navigation - optional, default is 30000
    """

    assert url, "URL is required"

    async def navigate_handler(browser: uc.Browser):
        print(f"Navigating to {url}")
        tab = await browser.get(url)
        return await create_success_response(f"Navigated to {url}")

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), navigate_handler
    )


DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads")
SCREENSHOTS = {}


@mcp.tool()
async def browser_screenshot(
        name: str,
        storeBase64: bool = True,
        downloadsDir: str = None,
):
    """Take a screenshot of the current page or a specific element

    Args:
        name: The name of the screenshot - required, default is "screenshot"
        storeBase64: Whether to store the screenshot as a base64 string - optional, default is True
        downloadsDir: The directory to save the screenshot to - optional, default is the user's Downloads directory
    """
    name = name or "screenshot"

    async def screenshot_handler(browser: uc.Browser):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        filename = f"{name}-{timestamp}.png"
        download_dir = downloadsDir or DEFAULT_DOWNLOAD_PATH

        os.makedirs(download_dir, exist_ok=True)

        output_path = os.path.join(download_dir, filename)

        # Get the main tab
        tab = browser.main_tab
        await tab.save_screenshot(output_path)

        messages = [f"Screenshot saved to: {os.path.relpath(output_path, os.getcwd())}"]

        if storeBase64:
            # Read the saved screenshot and convert to base64
            with open(output_path, 'rb') as f:
                screenshot_base64 = base64.b64encode(f.read()).decode('utf-8')
            SCREENSHOTS[name] = screenshot_base64
            # todo: notifications/resources/list_changed
            messages.append(f"Screenshot also stored in memory with name: {name}")

        return await create_success_response(messages)

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), screenshot_handler
    )


@mcp.tool()
async def browser_click(
        selector: str,
):
    """Click an element on the page

    Args:
        selector: The selector of the element to click - required
    """
    assert selector, "Selector is required"

    async def click_handler(browser: uc.Browser):
        tab = browser.main_tab
        element = await tab.find(selector)
        await element.click()
        return await create_success_response(f"Clicked element: {selector}")

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), click_handler
    )


@mcp.tool()
async def browser_iframe_click(
        iframeSelector: str,
        selector: str,
):
    """Click an element inside an iframe on the page

    Args:
        iframeSelector: The selector of the iframe - required
        selector: The selector of the element to click - required
    """
    assert iframeSelector, "Iframe selector is required"
    assert selector, "Selector is required"

    async def iframe_click_handler(browser: uc.Browser):
        tab = browser.main_tab
        # In nodriver, we need to get the iframe element and its content document
        iframe_element = await tab.find(iframeSelector)
        # Get the frame's content
        frame = await iframe_element.content_document
        # Find and click the element within the iframe
        element = await frame.find(selector)
        await element.click()
        return await create_success_response(
            f"Clicked element {selector} inside iframe {iframeSelector}"
        )

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), iframe_click_handler
    )


@mcp.tool()
async def browser_fill(
        selector: str,
        value: str,
):
    """fill out an input field

    Args:
        selector: CSS selector for input field - required
        value: The value to fill - required
    """
    assert selector, "Selector is required"
    assert value, "Value is required"

    async def fill_handler(browser: uc.Browser):
        tab = browser.main_tab
        element = await tab.find(selector)
        await element.send_keys(value)
        return await create_success_response(f"Filled {selector} with: {value}")

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), fill_handler
    )


@mcp.tool()
async def browser_select(
        selector: str,
        value: str,
):
    """Select an element on the page with Select tag

    Args:
        selector: CSS selector for element to select - required
        value: The value to select - required
    """
    assert selector, "Selector is required"
    assert value, "Value is required"

    async def select_handler(browser: uc.Browser):
        tab = browser.main_tab
        # Use JavaScript to set the select value in nodriver
        script = f"""
        const select = document.querySelector('{selector}');
        if (select) {{
            select.value = '{value}';
            select.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return true;
        }}
        return false;
        """
        result = await tab.evaluate(script)
        if result:
            return await create_success_response(f"Selected {selector} with: {value}")
        raise Exception(f"Could not find select element: {selector}")

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), select_handler
    )


@mcp.tool()
async def browser_hover(
        selector: str,
):
    """Hover over an element on the page

    Args:
        selector: CSS selector for element to hover over - required
    """
    assert selector, "Selector is required"

    async def hover_handler(browser: uc.Browser):
        tab = browser.main_tab
        element = await tab.find(selector)
        await element.mouse_move()
        return await create_success_response(f"Hovered over {selector}")

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), hover_handler
    )


@mcp.tool()
async def browser_evalute(
        script: str,
):
    """Evaluate a JavaScript expression in the browser console

    Args:
        script: The JavaScript expression to evaluate - required
    """
    assert script, "Script is required"

    async def evaluate_handler(browser: uc.Browser):
        tab = browser.main_tab
        result = await tab.evaluate(script)
        return await create_success_response(
            [
                "Executed script:",
                f"{script}",
                "Result:",
                f"{result}",
            ]
        )

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), evaluate_handler
    )


@mcp.tool()
async def browser_close():
    """Close the browser and release all resources"""
    await reset_browser_state()
    return await create_success_response("Browser closed successfully")


@mcp.tool()
async def browser_get_visible_text():
    """Get the visible text of the current page"""

    async def get_visible_text_handler(browser: uc.Browser):
        tab = browser.main_tab
        # Use JavaScript to get all visible text content
        script = """
        return Array.from(document.body.querySelectorAll('*'))
            .filter(el => {
                const style = window.getComputedStyle(el);
                return !!(el.textContent.trim()) &&
                       style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       style.opacity !== '0';
            })
            .map(el => el.textContent.trim())
            .filter(text => text)
            .join('\\n');
        """
        visible_text = await tab.evaluate(script)
        return await create_success_response(visible_text)

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), get_visible_text_handler
    )


@mcp.tool()
async def browser_get_visible_html():
    """Get the HTML of the current page"""

    async def get_visible_html_handler(browser: uc.Browser):
        tab = browser.main_tab
        html = await tab.get_content()
        return await create_success_response(html)

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), get_visible_html_handler
    )


@mcp.tool()
async def browser_go_back():
    """Navigate back in browser history"""

    async def go_back_handler(browser: uc.Browser):
        tab = browser.main_tab
        await tab.back()
        return await create_success_response("Navigated back in browser history")

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), go_back_handler
    )


@mcp.tool()
async def browser_go_forward():
    """Navigate forward in browser history"""

    async def go_forward_handler(browser: uc.Browser):
        tab = browser.main_tab
        await tab.forward()
        return await create_success_response("Navigated forward in browser history")

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), go_forward_handler
    )


@mcp.tool()
async def browser_drag(
        sourceSelector: str,
        targetSelector: str,
):
    """Drag an element to another element

    Args:
        sourceSelector: The selector for the element to drag - required
        targetSelector: The selector for the target location - required
    """
    assert sourceSelector, "Source selector is required"
    assert targetSelector, "Target selector is required"

    async def drag_handler(browser: uc.Browser):
        tab = browser.main_tab
        source = await tab.find(sourceSelector)
        target = await tab.find(targetSelector)

        # Get coordinates for drag and drop
        source_box = await source.get_box_model()
        target_box = await target.get_box_model()

        # Perform drag and drop using mouse actions
        await source.mouse_move()
        await tab.mouse_down()
        await target.mouse_move()
        await tab.mouse_up()

        return await create_success_response(
            f"Dragged {sourceSelector} to {targetSelector}"
        )

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), drag_handler
    )


@mcp.tool()
async def browser_press_key(
        key: str,
        selector: str = None,
):
    """Press a key on the keyboard

    Args:
        key: The key to press - required, (e.g. 'Enter', 'ArrowDown', 'a')
        selector: Optional CSS selector to focus on before pressing the key - optional
    """
    assert key, "Key is required"

    async def press_key_handler(browser: uc.Browser):
        tab = browser.main_tab

        # If selector is provided, find and focus the element
        if selector:
            element = await tab.find(selector)
            await element.click()  # Click to focus

        # Map key names to nodriver key codes
        # nodriver uses similar key names as Chrome DevTools Protocol
        key_to_send = key

        # Send the key press
        await tab.send_keys(key_to_send)

        if selector:
            return await create_success_response(f"Pressed key '{key}' on element '{selector}'")
        else:
            return await create_success_response(f"Pressed key '{key}'")

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), press_key_handler
    )


@mcp.tool()
async def browser_save_as_pdf(
        outputPath: str,
        filename: str = "page.pdf",
        format: str = 'A4',
        printBackground: bool = True,
        margin: dict = None,
):
    """Save the current page as a PDF

    Args:
        outputPath: The path to save the PDF to - required
        filename: The name of the PDF file - optional, default is "page.pdf"
        format: The format of the PDF - optional, default is "A4" (e.g. "A4", "LETTER", "LEGAL", "TABLOID")
        printBackground: Whether to print the background - optional, default is True
        margin: The margin of the PDF - optional, default is None (e.g. {"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"})
    """
    assert outputPath, "Output path is required"

    margin = margin or {"top": 0, "right": 0, "bottom": 0, "left": 0}

    async def save_as_pdf_handler(browser: uc.Browser):
        # Ensure output path exists
        os.makedirs(outputPath, exist_ok=True)

        # Build full file path
        full_path = os.path.join(outputPath, filename)

        tab = browser.main_tab

        # Use CDP to print to PDF
        pdf_data = await tab.send(
            "Page.printToPDF",
            {
                "printBackground": printBackground,
                "paperWidth": 8.27 if format == "A4" else 8.5,  # inches
                "paperHeight": 11.69 if format == "A4" else 11,  # inches
                "marginTop": margin.get('top', 0),
                "marginRight": margin.get('right', 0),
                "marginBottom": margin.get('bottom', 0),
                "marginLeft": margin.get('left', 0),
            }
        )

        # Decode and save PDF
        with open(full_path, 'wb') as f:
            f.write(base64.b64decode(pdf_data['data']))

        return await create_success_response(f"Saved page as PDF to {full_path}")

    return await tool.safe_execute(
        ToolContext(browser=await ensure_browser()), save_as_pdf_handler
    )


if __name__ == "__main__":
    asyncio.run(mcp.run_stdio_async())
