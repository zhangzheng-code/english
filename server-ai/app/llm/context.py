from contextvars import ContextVar

# 全局唯一的 chat_model_var 状态机，默认为 "flash"
chat_model_var: ContextVar[str] = ContextVar("chat_model_var", default="flash")


def set_model_type(model_type: str) -> None:
    """安全设置当前协程上下文的模型类型"""
    chat_model_var.set(model_type)


def get_model_type() -> str:
    """安全获取当前协程上下文的模型类型"""
    return chat_model_var.get()


# 全局唯一的 chat_image_url_var，默认为 None
chat_image_url_var: ContextVar[str | None] = ContextVar("chat_image_url_var", default=None)


def set_image_url(image_url: str | None) -> None:
    """安全设置当前协程上下文的图片 URL"""
    chat_image_url_var.set(image_url)


def get_image_url() -> str | None:
    """安全获取当前协程上下文的图片 URL"""
    return chat_image_url_var.get()

