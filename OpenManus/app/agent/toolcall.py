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

            # Add assistant response to messages
            self.messages += [response]

            # Process tool calls if any
            if response.tool_calls:
                self.tool_calls = response.tool_calls
                return True
            else:
                # No tool calls, check if we're done
                if response.content and any(
                    special_name in response.content.lower()
                    for special_name in self.special_tool_names
                ):
                    self.state = AgentState.COMPLETED
                    return False
                else:
                    # Continue with next step
                    return True

        except TokenLimitExceeded as e:
            logger.warning(f"Token limit exceeded: {e}")
            self.state = AgentState.ERROR
            return False
        except Exception as e:
            logger.error(f"Error in think: {e}")
            self.state = AgentState.ERROR
            return False

    async def act(self) -> bool:
        """Execute tool calls from the think phase"""
        if not self.tool_calls:
            logger.warning(TOOL_CALL_REQUIRED)
            return False

        try:
            # Process each tool call
            for tool_call in self.tool_calls:
                # Skip if no function call
                if not tool_call.function:
                    continue

                # Get tool name and arguments
                tool_name = tool_call.function.name
                tool_args = {}

                # Parse arguments if provided
                if tool_call.function.arguments:
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        logger.error(
                            f"Invalid JSON in tool arguments: {tool_call.function.arguments}"
                        )
                        continue

                # Check if tool exists
                if tool_name not in self.available_tools:
                    logger.warning(f"Tool '{tool_name}' not found")
                    continue

                # Execute the tool
                logger.info(f"🔧 Activating tool: '{tool_name}'...")
                tool = self.available_tools[tool_name]
                result = await tool.execute(**tool_args)

                # Handle special tools
                if tool_name in self.special_tool_names:
                    if tool_name == Terminate().name:
                        self.state = AgentState.COMPLETED
                        return False

                # Add tool result to messages
                self.messages += [
                    Message.tool_message(
                        content=f"Observed output of cmd `{tool_name}` executed:\n{result}",
                        tool_call_id=tool_call.id,
                    )
                ]

            # Clear tool calls for next iteration
            self.tool_calls = []
            return True

        except Exception as e:
            logger.error(f"Error in act: {e}")
            self.state = AgentState.ERROR
            return False

    async def run(self) -> str:
        """Run the agent until completion or max steps reached"""
        self.state = AgentState.RUNNING
        self.current_step = 0

        while self.state == AgentState.RUNNING and self.current_step < self.max_steps:
            self.current_step += 1
            logger.info(f"Executing step {self.current_step}/{self.max_steps}")

            # Think phase
            if not await self.think():
                break

            # Act phase
            if not await self.act():
                break

        # Return final response
        for msg in reversed(self.messages):
            if msg.role == "assistant" and msg.content and not msg.tool_calls:
                return msg.content
        
        return "Task completed without a final response."

    async def run_with_streaming(self) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        """Run the agent with streaming responses"""
        self.state = AgentState.RUNNING
        self.current_step = 0
        accumulated_content = ""
        accumulated_tool_calls = []

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

                # Reset accumulators
                accumulated_content = ""
                accumulated_tool_calls = []

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
                        accumulated_content += chunk["content"]
                        yield chunk["content"]
                    
                    if chunk.get("tool_calls"):
                        accumulated_tool_calls.extend(chunk["tool_calls"])
                
                # Create the complete response message
                from app.schema import ToolCall as SchemaToolCall
                tool_calls = []
                if accumulated_tool_calls:
                    for tc in accumulated_tool_calls:
                        tool_calls.append(SchemaToolCall(
                            id=tc.get("id", ""),
                            type=tc.get("type", "function"),
                            function={
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"]
                            }
                        ))

                # Create assistant message
                response = Message(
                    role="assistant",
                    content=accumulated_content if accumulated_content else None,
                    tool_calls=tool_calls if tool_calls else None
                )

                # Add assistant response to messages
                self.messages += [response]

                # Process tool calls if any
                if response.tool_calls:
                    self.tool_calls = response.tool_calls
                    
                    # Act phase
                    if not await self.act():
                        break
                else:
                    # No tool calls, check if we're done
                    if response.content and any(
                        special_name in response.content.lower()
                        for special_name in self.special_tool_names
                    ):
                        self.state = AgentState.COMPLETED
                        break
            
            except Exception as e:
                logger.error(f"Error in streaming run: {e}")
                yield {"error": str(e)}
                self.state = AgentState.ERROR
                break

        # Return final response
        for msg in reversed(self.messages):
            if hasattr(msg, 'role') and msg.role == "assistant" and hasattr(msg, 'content') and msg.content and not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                yield {"final": msg.content}
                return
        
        yield {"final": "Task completed without a final response."}

