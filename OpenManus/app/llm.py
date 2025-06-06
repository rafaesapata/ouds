                    if delta.content:
                        result["content"] = delta.content
                    
                    if delta.tool_calls:
                        try:
                            result["tool_calls"] = []
                            for tool_call in delta.tool_calls:
                                try:
                                    # Verificar se tool_call tem os atributos necessários
                                    if not hasattr(tool_call, "id") or not hasattr(tool_call, "type"):
                                        logger.warning(f"Tool call missing required attributes: {tool_call}")
                                        continue
                                        
                                    # Verificar se function existe e tem os atributos necessários
                                    if not hasattr(tool_call, "function"):
                                        logger.warning(f"Tool call missing function attribute: {tool_call}")
                                        continue
                                        
                                    # Verificar se function tem os atributos name e arguments
                                    function = tool_call.function
                                    if not hasattr(function, "name") or not hasattr(function, "arguments"):
                                        logger.warning(f"Function missing required attributes: {function}")
                                        continue
                                    
                                    # Adicionar o tool call ao resultado com verificações de segurança
                                    result["tool_calls"].append({
                                        "id": getattr(tool_call, "id", ""),
                                        "type": getattr(tool_call, "type", "function"),
                                        "function": {
                                            "name": getattr(function, "name", ""),
                                            "arguments": getattr(function, "arguments", "{}"),
                                        }
                                    })
                                except Exception as tc_error:
                                    logger.warning(f"Error processing individual tool call: {tc_error}")
                                    continue
                        except Exception as tc_list_error:
                            logger.warning(f"Error processing tool calls list: {tc_list_error}")
                    
                    if result:
                        yield result

        except TokenLimitExceeded as e:
            # Re-raise token limit exceptions
            raise e
        except (AuthenticationError, APIError, RateLimitError) as e:
            # Log and re-raise OpenAI errors
            logger.error(f"OpenAI API error: {str(e)}")
            raise e
        except Exception as e:
            # Log and re-raise other exceptions
            logger.error(f"Unexpected error in LLM.ask_tool_streaming: {str(e)}")
            raise e

