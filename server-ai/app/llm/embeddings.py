from langchain_core.embeddings import Embeddings

class MockEmbeddings(Embeddings):
    """
    一个本地 Mock Embedding 类，生成 1536 维度的虚拟向量，
    用于本地调试、测试，避免对外部 API Key 的依赖。
    """
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # 对每个文本生成一个简单的确定性伪向量
        results = []
        for text in texts:
            val = float(len(text) % 100) / 100.0
            results.append([val] * 1536)
        return results

    def embed_query(self, text: str) -> list[float]:
        val = float(len(text) % 100) / 100.0
        return [val] * 1536


def get_embeddings() -> Embeddings:
    """
    统一的 Embedding 获取入口：
    可在此处切换到实际的 OpenAIEmbeddings, HuggingFaceEmbeddings 等。
    默认返回 MockEmbeddings 以保持离线运行能力。
    """
    return MockEmbeddings()
