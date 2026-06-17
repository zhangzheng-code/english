"""Windows 兼容入口：强制使用 SelectorEventLoop（psycopg 要求）"""
import asyncio
import selectors
import sys


def _loop_factory():
    """创建 SelectorEventLoop（Windows 下 psycopg 要求）"""
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


if __name__ == "__main__":
    import uvicorn

    if sys.platform == "win32":
        # 用 asyncio.run 的 loop_factory 参数确保整个生命周期使用 SelectorEventLoop
        async def _main():
            config = uvicorn.Config("app.main:app", host="0.0.0.0", port=3002, log_level="info")
            server = uvicorn.Server(config)
            await server.serve()

        asyncio.run(_main(), loop_factory=_loop_factory)
    else:
        uvicorn.run("app.main:app", host="0.0.0.0", port=3002, log_level="info")
