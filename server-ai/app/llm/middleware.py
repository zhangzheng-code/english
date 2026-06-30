from langchain.agents.middleware import wrap_model_call
from app.llm.context import get_model_type, get_image_url
from app.llm.models import create_deepseek, create_deepseek_reasoner
from langchain_core.messages import HumanMessage


@wrap_model_call
async def dynamic_model_selector(request, handler):
    """
    根据当前协程上下文的标签动态替换底层的物理模型实例，
    并在含有图片上下文时动态转换为多模态消息体。
    """
    model_type = get_model_type()
    
    # 动态选择目标模型实例
    if model_type == "reasoner":
        target_model = create_deepseek_reasoner()
    else:
        target_model = create_deepseek()
        
    image_url = get_image_url()
    override_kwargs = {"model": target_model}

    messages = list(getattr(request, "messages", None) or [])

    # 清洗历史消息：将历史中所有 image_url 内容降级为纯文本
    # 防止无图请求携带旧的多模态内容导致 DeepSeek 400
    sanitized_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage) and isinstance(msg.content, list):
            # 只保留 text 部分，剥除 image_url
            text_parts = [
                part.get("text", "") for part in msg.content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            clean_text = " ".join(text_parts).strip()
            sanitized_messages.append(HumanMessage(
                content=clean_text or "[图片消息]",
                id=msg.id,
                additional_kwargs=msg.additional_kwargs,
                response_metadata=msg.response_metadata
            ))
        else:
            sanitized_messages.append(msg)

    # 重构最后一条用户消息为多模态格式（仅当本次请求携带图片时）
    if image_url and sanitized_messages:
        last_msg = sanitized_messages[-1]
        if isinstance(last_msg, HumanMessage) and isinstance(last_msg.content, str):
            new_content = [
                {"type": "text", "text": last_msg.content},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
            new_last_msg = HumanMessage(
                content=new_content,
                id=last_msg.id,
                additional_kwargs=last_msg.additional_kwargs,
                response_metadata=last_msg.response_metadata
            )
            sanitized_messages = sanitized_messages[:-1] + [new_last_msg]

    override_kwargs["messages"] = sanitized_messages
        
    # 不可变重构请求参数并覆写物理模型与消息列表
    overridden_request = request.override(**override_kwargs)
    
    # 执行下游处理并返回结果
    return await handler(overridden_request)

