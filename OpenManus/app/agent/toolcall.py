import asyncio
import json
from typing import Any, List, Optional, Union, Dict, AsyncGenerator

from pydantic import Field

from app.agent.react import ReActAgent
from app.exceptions import TokenLimitExceeded
from app.logger import logger
from app.prompt.toolcall import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.schema import TOOL_CHOICE_TYPE, AgentState, Message, ToolCall, ToolChoice
from app.tool import CreateChatCompletion, Terminate, ToolCollection


TOOL_CALL_REQUIRED = "Tool calls required but none provided"


class ToolCallAgent(ReActAgent):
    """Base agent class for handling tool/function calls with enhanced abstraction"""

    name: str = "toolcall"
    description: str = "an agent that can execute tool calls."

    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT

    available_tools: ToolCollection = ToolCollection(
        CreateChatCompletion(), Terminate()
    )
    tool_choices: TOOL_CHOICE_TYPE = ToolChoice.AUTO  # type: ignore
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])

    tool_calls: List[ToolCall] = Field(default_factory=list)
    _current_base64_image: Optional[str] = None

    max_steps: int = 30
    max_observe: Optional[Union[int, bool]] = None

    async def think(self) -> bool:
        """Process current state and decide next actions using tools"""
        if self.next_step_prompt:
            user_msg = Message.user_message(self.next_step_prompt)
            self.messages += [user_msg]

        try:
            # Get response with tool options
            response = await self.llm.ask_tool(
                messages=self.messages,
                system_msgs=(
                    [Message.system_message(self.system_prompt)]
                    if self.system_prompt
                    else None
                ),
                tools=self.available_tools.to_openai_tools(),
                tool_choice=self.tool_choices,
                base64_image=self._current_base64_image,
            )
            self._current_base64_image = None  # Reset after use

            # Process response
            if response.tool_calls:
                self.tool_calls = response.tool_calls
                self.messages.append(response)
                return True
            else:
                # No tool calls, just add response to messages
                self.messages.append(response)
                return False

        except TokenLimitExceeded as e:
            logger.warning(f"Token limit exceeded: {e}")
            # Truncate messages to handle token limit
            self._truncate_messages()
            return await self.think()  # Retry with truncated messages

    async def act(self) -> bool:
        """Execute tool calls from the last response"""
        if not self.tool_calls:
            logger.warning(TOOL_CALL_REQUIRED)
            return False

        for tool_call in self.tool_calls:
            # Check for special tools
            if tool_call.function.name in self.special_tool_names:
                # Handle special tools like termination
                if tool_call.function.name == Terminate().name:
                    self.state = AgentState.FINISHED
                    return False

            # Execute the tool
            tool = self.available_tools.get(tool_call.function.name)
            if not tool:
                logger.warning(f"Tool {tool_call.function.name} not found")
                continue

            try:
                logger.info(f"🔧 Activating tool: '{tool_call.function.name}'...")
                args = json.loads(tool_call.function.arguments)
                result = await tool.execute(**args)
                logger.info(f"🎯 Tool '{tool_call.function.name}' completed its mission!")

                # Add tool result to messages
                tool_result = Message.tool_message(
                    content=str(result),
                    tool_call_id=tool_call.id,
                    name=tool_call.function.name,
                )
                self.messages.append(tool_result)

            except Exception as e:
                logger.error(f"❌ Error executing tool {tool_call.function.name}: {e}")
                # Add error message as tool result
                error_msg = f"Error: {tool_call.function.name} failed: {str(e)}"
                tool_result = Message.tool_message(
                    content=error_msg,
                    tool_call_id=tool_call.id,
                    name=tool_call.function.name,
                )
                self.messages.append(tool_result)

        # Reset tool calls after execution
        self.tool_calls = []
        return True

    async def observe(self) -> bool:
        """Observe the environment after actions (placeholder for subclasses)"""
        return True

    async def run(self) -> str:
        """Run the agent until completion or max steps reached"""
        self.state = AgentState.RUNNING
        self.current_step = 0

        while self.state == AgentState.RUNNING and self.current_step < self.max_steps:
            self.current_step += 1
            logger.info(f"Executing step {self.current_step}/{self.max_steps}")

            # Think phase
            thought_result = await self.think()
            if not thought_result or self.state != AgentState.RUNNING:
                break

            # Act phase
            act_result = await self.act()
            if not act_result or self.state != AgentState.RUNNING:
                break

            # Observe phase (optional)
            if self.max_observe:
                observe_result = await self.observe()
                if not observe_result or self.state != AgentState.RUNNING:
                    break

        # Return the final response
        if self.messages and self.messages[-1].role == "assistant":
            return self.messages[-1].content or ""
        
        # Find the last assistant message with content
        for msg in reversed(self.messages):
            if msg.role == "assistant" and msg.content:
                return msg.content
        
        return "Task completed without a final response."

    async def run_with_streaming(self) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        """Run the agent with streaming responses"""
        self.state = AgentState.RUNNING
        self.current_step = 0

        while self.state == AgentState.RUNNING and self.current_step < self.max_steps:
            self.current_step += 1
            logger.info(f"Executing step {self.current_step}/{self.max_steps}")

            # Yield status update
            yield {"step": self.current_step, "max_steps": self.max_steps}

            # Think phase with streaming
            try:
                if self.next_step_prompt:
                    user_msg = Message.user_message(self.next_step_prompt)
                    self.messages += [user_msg]

                # Get response with tool options and streaming
                async for chunk in self.llm.ask_tool_streaming(
                    messages=self.messages,
                    system_msgs=(
                        [Message.system_message(self.system_prompt)]
                        if self.system_prompt
                        else None
                    ),
                    tools=self.available_tools.to_openai_tools(),
                    tool_choice=self.tool_choices,
                    base64_image=self._current_base64_image,
                ):
                    if chunk.get("content"):
                        yield chunk["content"]
                
                # Get the final response
                response = await self.llm.ask_tool(
                    messages=self.messages,
                    system_msgs=(
                        [Message.system_message(self.system_prompt)]
                        if self.system_prompt
                        else None
                    ),
                    tools=self.available_tools.to_openai_tools(),
                    tool_choice=self.tool_choices,
                    base64_image=self._current_base64_image,
                )
                self._current_base64_image = None  # Reset after use

                # Process response
                if response.tool_calls:
                    self.tool_calls = response.tool_calls
                    self.messages.append(response)
                else:
                    # No tool calls, just add response to messages
                    self.messages.append(response)
                    break

            except TokenLimitExceeded as e:
                logger.warning(f"Token limit exceeded: {e}")
                # Truncate messages to handle token limit
                self._truncate_messages()
                continue

            # Act phase
            if not self.tool_calls:
                logger.warning(TOOL_CALL_REQUIRED)
                break

            for tool_call in self.tool_calls:
                # Check for special tools
                if tool_call.function.name in self.special_tool_names:
                    # Handle special tools like termination
                    if tool_call.function.name == Terminate().name:
                        self.state = AgentState.FINISHED
                        break

                # Execute the tool
                tool = self.available_tools.get(tool_call.function.name)
                if not tool:
                    logger.warning(f"Tool {tool_call.function.name} not found")
                    continue

                try:
                    logger.info(f"🔧 Activating tool: '{tool_call.function.name}'...")
                    args = json.loads(tool_call.function.arguments)
                    result = await tool.execute(**args)
                    logger.info(f"🎯 Tool '{tool_call.function.name}' completed its mission!")

                    # Add tool result to messages
                    tool_result = Message.tool_message(
                        content=str(result),
                        tool_call_id=tool_call.id,
                        name=tool_call.function.name,
                    )
                    self.messages.append(tool_result)

                except Exception as e:
                    logger.error(f"❌ Error executing tool {tool_call.function.name}: {e}")
                    # Add error message as tool result
                    error_msg = f"Error: {tool_call.function.name} failed: {str(e)}"
                    tool_result = Message.tool_message(
                        content=error_msg,
                        tool_call_id=tool_call.id,
                        name=tool_call.function.name,
                    )
                    self.messages.append(tool_result)

            # Reset tool calls after execution
            self.tool_calls = []

            # Observe phase (optional)
            if self.max_observe:
                observe_result = await self.observe()
                if not observe_result or self.state != AgentState.RUNNING:
                    break

        # Return the final status
        yield {"status": "completed", "steps": self.current_step}

    def _truncate_messages(self, keep_last: int = 5) -> None:
        """Truncate message history to handle token limits"""
        if len(self.messages) <= keep_last:
            return

        # Keep system messages and the last few messages
        system_msgs = [msg for msg in self.messages if msg.role == "system"]
        last_msgs = self.messages[-keep_last:]
        
        # Create a truncation message
        truncation_msg = Message.system_message(
            "[Message history truncated due to token limit]"
        )
        
        # Rebuild messages with system, truncation notice, and recent messages
        self.messages = system_msgs + [truncation_msg] + last_msgs
        logger.info(f"Truncated message history to {len(self.messages)} messages")

