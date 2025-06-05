import asyncio
import base64
import json
from typing import Generic, Optional, TypeVar

from browser_use import Browser as BrowserUseBrowser
from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.dom.service import DomService
from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.config import config
from app.llm import LLM
from app.tool.base import BaseTool, ToolResult
from app.tool.web_search import WebSearch


_BROWSER_DESCRIPTION = """\
A powerful browser automation tool that allows interaction with web pages through various actions.
* This tool provides commands for controlling a browser session, navigating web pages, and extracting information
* It maintains state across calls, keeping the browser session alive until explicitly closed
* Use this when you need to browse websites, fill forms, click buttons, extract content, or perform web searches
* Each action requires specific parameters as defined in the tool's dependencies

Key capabilities include:
* Navigation: Go to specific URLs, go back, search the web, or refresh pages
* Interaction: Click elements, input text, select from dropdowns, send keyboard commands
* Scrolling: Scroll up/down by pixel amount or scroll to specific text
* Content extraction: Extract and analyze content from web pages based on specific goals
* Tab management: Switch between tabs, open new tabs, or close tabs

Note: When using element indices, refer to the numbered elements shown in the current browser state.
"""

Context = TypeVar("Context")


class BrowserUseTool(BaseTool, Generic[Context]):
    name: str = "browser_use"
    description: str = _BROWSER_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "go_to_url",
                    "click_element",
                    "input_text",
                    "scroll_down",
                    "scroll_up",
                    "scroll_to_text",
                    "send_keys",
                    "get_dropdown_options",
                    "select_dropdown_option",
                    "go_back",
                    "web_search",
                    "wait",
                    "extract_content",
                    "switch_tab",
                    "open_tab",
                    "close_tab",
                ],
                "description": "The browser action to perform",
            },
            "url": {
                "type": "string",
                "description": "URL for 'go_to_url' or 'open_tab' actions",
            },
            "index": {
                "type": "integer",
                "description": "Element index for 'click_element', 'input_text', 'get_dropdown_options', or 'select_dropdown_option' actions",
            },
            "text": {
                "type": "string",
                "description": "Text for 'input_text', 'scroll_to_text', or 'select_dropdown_option' actions",
            },
            "scroll_amount": {
                "type": "integer",
                "description": "Pixels to scroll (positive for down, negative for up) for 'scroll_down' or 'scroll_up' actions",
            },
            "tab_id": {
                "type": "integer",
                "description": "Tab ID for 'switch_tab' action",
            },
            "query": {
                "type": "string",
                "description": "Search query for 'web_search' action",
            },
            "goal": {
                "type": "string",
                "description": "Extraction goal for 'extract_content' action",
            },
            "keys": {
                "type": "string",
                "description": "Keys to send for 'send_keys' action",
            },
            "seconds": {
                "type": "integer",
                "description": "Seconds to wait for 'wait' action",
            },
        },
        "required": ["action"],
        "dependencies": {
            "go_to_url": ["url"],
            "click_element": ["index"],
            "input_text": ["index", "text"],
            "switch_tab": ["tab_id"],
            "open_tab": ["url"],
            "scroll_down": ["scroll_amount"],
            "scroll_up": ["scroll_amount"],
            "scroll_to_text": ["text"],
            "send_keys": ["keys"],
            "get_dropdown_options": ["index"],
            "select_dropdown_option": ["index", "text"],
            "go_back": [],
            "web_search": ["query"],
            "wait": ["seconds"],
            "extract_content": ["goal"],
        },
    }

    lock: asyncio.Lock = Field(default_factory=asyncio.Lock)
    browser: Optional[BrowserUseBrowser] = Field(default=None, exclude=True)
    context: Optional[BrowserContext] = Field(default=None, exclude=True)
    dom_service: Optional[DomService] = Field(default=None, exclude=True)
    web_search_tool: WebSearch = Field(default_factory=WebSearch, exclude=True)

    # Context for generic functionality
    tool_context: Optional[Context] = Field(default=None, exclude=True)

    llm: Optional[LLM] = Field(default_factory=LLM)

    @field_validator("parameters", mode="before")
    def validate_parameters(cls, v: dict, info: ValidationInfo) -> dict:
        if not v:
            raise ValueError("Parameters cannot be empty")
        return v

    async def _ensure_browser_initialized(self) -> BrowserContext:
        """Ensure browser and context are initialized."""
        if self.browser is None:
            browser_config_kwargs = {"headless": True, "disable_security": True}

            if config.browser_config:
                from browser_use.browser.browser import ProxySettings

                # handle proxy settings.
                if config.browser_config.proxy and config.browser_config.proxy.server:
                    browser_config_kwargs["proxy"] = ProxySettings(
                        server=config.browser_config.proxy.server,
                        username=config.browser_config.proxy.username,
                        password=config.browser_config.proxy.password,
                    )

                browser_attrs = [
                    "headless",
                    "disable_security",
                    "extra_chromium_args",
                    "chrome_instance_path",
                    "wss_url",
                    "cdp_url",
                ]

                for attr in browser_attrs:
                    value = getattr(config.browser_config, attr, None)
                    if value is not None:
                        if not isinstance(value, list) or value:
                            browser_config_kwargs[attr] = value

            # Forçar modo headless para evitar problemas com X server
            browser_config_kwargs["headless"] = True
            
            # Criar configuração do browser
            browser_config = BrowserConfig(**browser_config_kwargs)
            
            # Inicializar o browser com a configuração
            self.browser = BrowserUseBrowser(browser_config)

        if self.context is None:
            context_config = BrowserContextConfig()

            # if there is context config in the config, use it.
            if (
                config.browser_config
                and hasattr(config.browser_config, "new_context_config")
                and config.browser_config.new_context_config
            ):
                context_config = config.browser_config.new_context_config

            # Criar contexto do browser
            self.context = await self.browser.new_context(context_config)
            self.dom_service = DomService(await self.context.get_current_page())

        return self.context

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        index: Optional[int] = None,
        text: Optional[str] = None,
        scroll_amount: Optional[int] = None,
        tab_id: Optional[int] = None,
        query: Optional[str] = None,
        goal: Optional[str] = None,
        keys: Optional[str] = None,
        seconds: Optional[int] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Execute a specified browser action.

        Args:
            action: The browser action to perform
            url: URL for navigation or new tab
            index: Element index for click or input actions
            text: Text for input action or search query
            scroll_amount: Pixels to scroll for scroll action
            tab_id: Tab ID for switch_tab action
            query: Search query for Google search
            goal: Extraction goal for content extraction
            keys: Keys to send for keyboard actions
            seconds: Seconds to wait
            **kwargs: Additional arguments

        Returns:
            ToolResult with the action's output or error
        """
        async with self.lock:
            try:
                context = await self._ensure_browser_initialized()

                # Get max content length from config
                max_content_length = getattr(
                    config.browser_config, "max_content_length", 2000
                )

                # Navigation actions
                if action == "go_to_url":
                    if not url:
                        return ToolResult(
                            error="URL is required for 'go_to_url' action"
                        )
                    page = await context.get_current_page()
                    await page.goto(url)
                    await page.wait_for_load_state()
                    return ToolResult(output=f"Navigated to {url}")

                elif action == "go_back":
                    await context.go_back()
                    return ToolResult(output="Navigated back")

                elif action == "refresh":
                    await context.refresh_page()
                    return ToolResult(output="Refreshed current page")

                # Interaction actions
                elif action == "click_element":
                    if index is None:
                        return ToolResult(
                            error="Element index is required for 'click_element' action"
                        )
                    await self.dom_service.click_element(index)
                    return ToolResult(output=f"Clicked element at index {index}")

                elif action == "input_text":
                    if index is None or text is None:
                        return ToolResult(
                            error="Element index and text are required for 'input_text' action"
                        )
                    await self.dom_service.input_text(index, text)
                    return ToolResult(
                        output=f"Input text '{text}' into element at index {index}"
                    )

                elif action == "send_keys":
                    if not keys:
                        return ToolResult(
                            error="Keys are required for 'send_keys' action"
                        )
                    await self.dom_service.send_keys(keys)
                    return ToolResult(output=f"Sent keys: {keys}")

                # Dropdown actions
                elif action == "get_dropdown_options":
                    if index is None:
                        return ToolResult(
                            error="Element index is required for 'get_dropdown_options' action"
                        )
                    options = await self.dom_service.get_dropdown_options(index)
                    return ToolResult(
                        output=f"Dropdown options for element at index {index}: {options}"
                    )

                elif action == "select_dropdown_option":
                    if index is None or text is None:
                        return ToolResult(
                            error="Element index and option text are required for 'select_dropdown_option' action"
                        )
                    await self.dom_service.select_dropdown_option(index, text)
                    return ToolResult(
                        output=f"Selected option '{text}' from dropdown at index {index}"
                    )

                # Scrolling actions
                elif action == "scroll_down":
                    if scroll_amount is None:
                        return ToolResult(
                            error="Scroll amount is required for 'scroll_down' action"
                        )
                    await self.dom_service.scroll_down(scroll_amount)
                    return ToolResult(output=f"Scrolled down {scroll_amount} pixels")

                elif action == "scroll_up":
                    if scroll_amount is None:
                        return ToolResult(
                            error="Scroll amount is required for 'scroll_up' action"
                        )
                    await self.dom_service.scroll_up(scroll_amount)
                    return ToolResult(output=f"Scrolled up {scroll_amount} pixels")

                elif action == "scroll_to_text":
                    if not text:
                        return ToolResult(
                            error="Text is required for 'scroll_to_text' action"
                        )
                    await self.dom_service.scroll_to_text(text)
                    return ToolResult(output=f"Scrolled to text: {text}")

                # Tab management actions
                elif action == "switch_tab":
                    if tab_id is None:
                        return ToolResult(
                            error="Tab ID is required for 'switch_tab' action"
                        )
                    await context.switch_tab(tab_id)
                    return ToolResult(output=f"Switched to tab {tab_id}")

                elif action == "open_tab":
                    if not url:
                        return ToolResult(
                            error="URL is required for 'open_tab' action"
                        )
                    tab_id = await context.open_tab(url)
                    return ToolResult(output=f"Opened new tab with ID {tab_id}")

                elif action == "close_tab":
                    await context.close_tab()
                    return ToolResult(output="Closed current tab")

                # Search action
                elif action == "web_search":
                    if not query:
                        return ToolResult(
                            error="Query is required for 'web_search' action"
                        )
                    search_result = await self.web_search_tool.execute(query=query)
                    return search_result

                # Wait action
                elif action == "wait":
                    if seconds is None:
                        return ToolResult(
                            error="Seconds are required for 'wait' action"
                        )
                    await asyncio.sleep(seconds)
                    return ToolResult(output=f"Waited for {seconds} seconds")

                # Content extraction action
                elif action == "extract_content":
                    if not goal:
                        return ToolResult(
                            error="Goal is required for 'extract_content' action"
                        )
                    content = await self.dom_service.extract_content(goal)
                    if len(content) > max_content_length:
                        content = content[:max_content_length] + "... (truncated)"
                    return ToolResult(output=content)

                else:
                    return ToolResult(error=f"Unknown action: {action}")

            except Exception as e:
                return ToolResult(error=f"Browser action '{action}' failed: {str(e)}")

    async def get_current_state(self) -> ToolResult:
        """Get the current state of the browser."""
        async with self.lock:
            try:
                ctx = await self._ensure_browser_initialized()
                state = await ctx.get_state()
                viewport_height = 800  # Default viewport height

                # Take a screenshot for the state
                page = await ctx.get_current_page()

                await page.bring_to_front()
                await page.wait_for_load_state()

                screenshot = await page.screenshot(
                    full_page=True, animations="disabled", type="jpeg", quality=100
                )

                screenshot = base64.b64encode(screenshot).decode("utf-8")

                # Build the state info with all required fields
                state_info = {
                    "url": state.url,
                    "title": state.title,
                    "tabs": [tab.model_dump() for tab in state.tabs],
                    "help": "[0], [1], [2], etc., represent clickable indices corresponding to the elements listed. Clicking on these indices will navigate to or interact with the respective content behind them.",
                    "interactive_elements": (
                        state.element_tree.clickable_elements_to_string()
                        if state.element_tree
                        else ""
                    ),
                    "scroll_info": {
                        "pixels_above": getattr(state, "pixels_above", 0),
                        "pixels_below": getattr(state, "pixels_below", 0),
                        "total_height": getattr(state, "pixels_above", 0)
                        + getattr(state, "pixels_below", 0)
                        + viewport_height,
                    },
                    "viewport_height": viewport_height,
                }

                return ToolResult(
                    output=json.dumps(state_info, indent=4, ensure_ascii=False),
                    base64_image=screenshot,
                )
            except Exception as e:
                return ToolResult(error=f"Failed to get browser state: {str(e)}")

    async def cleanup(self):
        """Clean up browser resources."""
        async with self.lock:
            if self.context is not None:
                await self.context.close()
                self.context = None
                self.dom_service = None
            if self.browser is not None:
                await self.browser.close()
                self.browser = None

