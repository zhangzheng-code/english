import os
import io
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def evaluate_pronunciation(standard_text: str, user_text: str) -> dict:
    """
    音素级 Levenshtein 编辑距离评测算法：
    1. 利用 g2p_en 将标准单词和 ASR 识别出的单词转换成音素序列
    2. 计算音素编辑距离矩阵 (DP)
    3. 回溯矩阵路径，精确分析哪些音素是正确 (correct)、错读 (mispronounced)、漏读 (missing) 或多读 (extra)
    4. 返回百分制得分以及错音位置报告
    """
    from g2p_en import G2p
    
    # 缓存或初始化 G2p，g2p 在初次加载时可能会下载 nltk 资源
    try:
        g2p = G2p()
        std_raw = g2p(standard_text)
        usr_raw = g2p(user_text)
    except Exception as e:
        logger.warning(f"G2p initialization/execution failed: {e}. Falling back to character spelling distance.")
        # 如果 G2p 初始化有问题，退化到字符级匹配
        std_raw = list(standard_text.upper())
        usr_raw = list(user_text.upper())

    # 过滤空格和标点，仅保留有效的音素/字符标号
    std_phonemes = [p for p in std_raw if p.strip() and p.isalnum()]
    usr_phonemes = [p for p in usr_raw if p.strip() and p.isalnum()]

    m, n = len(std_phonemes), len(usr_phonemes)
    if m == 0 and n == 0:
        return {"score": 100, "details": []}
    if m == 0:
        return {"score": 0, "details": [{"phoneme": p, "status": "extra"} for p in usr_phonemes]}
    if n == 0:
        return {"score": 0, "details": [{"phoneme": p, "status": "missing"} for p in std_phonemes]}

    # DP 矩阵计算
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if std_phonemes[i - 1] == usr_phonemes[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # Deletion (missing)
                    dp[i][j - 1],      # Insertion (extra)
                    dp[i - 1][j - 1]   # Substitution (mispronounced)
                )

    # 计算发音得分
    distance = dp[m][n]
    max_len = max(m, n)
    score = int((1.0 - (distance / max_len)) * 100)

    # 回溯匹配细节
    i, j = m, n
    details = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and std_phonemes[i - 1] == usr_phonemes[j - 1]:
            details.append({"phoneme": std_phonemes[i - 1], "status": "correct"})
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            details.append({
                "phoneme": std_phonemes[i - 1],
                "status": "mispronounced",
                "user_phoneme": usr_phonemes[j - 1]
            })
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or dp[i][j] == dp[i - 1][j] + 1):
            details.append({"phoneme": std_phonemes[i - 1], "status": "missing"})
            i -= 1
        else:
            details.append({"phoneme": usr_phonemes[j - 1], "status": "extra"})
            j -= 1

    details.reverse()
    return {"score": max(0, score), "details": details}


async def transcribe_audio(audio_bytes: bytes) -> str:
    """
    将 PCM 或 WebM 音频数据通过 ASR (Speech-to-Text) 转换为文本。
    支持阿里云灵积 DashScope (sensevoice-v1 / paraformer) 或 OpenAI 兼容接口。
    如果音频为空或识别失败，默认返回空字符串 ""，防止静音被误判为满分。
    """
    import httpx
    
    fallback_text = ""
    if not audio_bytes or len(audio_bytes) < 100:
        return fallback_text
        
    api_key = settings.dashscope_api_key or settings.deepseek_api_key
    if not api_key:
        logger.warning("No ASR API key configured (dashscope_api_key). Returning empty string.")
        return fallback_text
        
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        # 优先使用阿里云灵积 DashScope 兼容接口，若未设置 dashscope 则回退 openai
        if settings.dashscope_api_key:
            url = "https://dashscope.aliyuncs.com/compatible-mode/v1/audio/transcriptions"
            model_name = getattr(settings, "asr_model", "sensevoice-v1")
        else:
            url = "https://api.openai.com/v1/audio/transcriptions"
            model_name = "whisper-1"

        files = {
            "file": ("audio.wav", audio_bytes, "audio/wav"),
            "model": (None, model_name),
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("text", "").strip()
            else:
                logger.warning(f"ASR API error ({response.status_code}): {response.text}")
                return fallback_text
    except Exception as e:
        logger.error(f"ASR Request failed: {e}")
        return fallback_text
