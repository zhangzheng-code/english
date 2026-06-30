import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel, Field

# 模拟的 Course Pydantic 结构
class CourseRecommendation(BaseModel):
    course_id: str
    title: str
    reason: str
    confidence: float

class CourseRecommendationList(BaseModel):
    recommendations: list[CourseRecommendation]


@pytest.mark.asyncio
@patch("app.socketio.sio")
async def test_payment_socketio_broadcast(mock_sio):
    """测试支付成功后，Room 广播同时推送 paymentSuccess 与 pay_success"""
    from app.socketio import emit_payment_success
    
    user_id = "test_user_vip"
    mock_sio.emit = AsyncMock()
    
    await emit_payment_success(user_id)
    
    # 验证是否广播了两个支付事件
    assert mock_sio.emit.call_count == 2
    calls = mock_sio.emit.call_args_list
    
    # 第一个 emit: paymentSuccess
    assert calls[0][0][0] == "paymentSuccess"
    assert calls[0][0][1] == user_id
    assert calls[0][1]["room"] == f"user_{user_id}"
    
    # 第二个 emit: pay_success
    assert calls[1][0][0] == "pay_success"
    assert calls[1][0][1] == {"success": True}
    assert calls[1][1]["room"] == f"user_{user_id}"


@pytest.mark.asyncio
@patch("clickhouse_connect.get_client")
@patch("app.services.recommend.create_deepseek")
async def test_recommendation_structured_output(mock_deepseek, mock_clickhouse):
    """测试 ClickHouse 行为特征聚合与大模型 structured_output 课程推荐逻辑"""
    from app.services.recommend import generate_recommendations
    
    user_id = "user_recommend_123"
    
    # Mock ClickHouse Client & Query
    mock_ch_client = MagicMock()
    mock_ch_client.query.return_value.result_rows = [
        ("click_word", '{"word": "allowance"}', "2026-06-28 12:00:00"),
        ("speech_practice", '{"duration": 120}', "2026-06-28 12:05:00")
    ]
    mock_clickhouse.return_value = mock_ch_client
    
    # Mock PostgreSQL Session
    mock_db = AsyncMock()
    mock_courses_result = MagicMock()
    mock_course = MagicMock()
    mock_course.id = "cuid_course_1"
    mock_course.name = "IELTS Oral Practice Master"
    mock_courses_result.scalars.return_value.all.return_value = [mock_course]
    mock_db.execute.return_value = mock_courses_result
    
    # Mock LangChain with_structured_output as AsyncMock
    mock_model = MagicMock()
    mock_structured_model = AsyncMock()
    mock_structured_model.ainvoke.return_value = CourseRecommendationList(
        recommendations=[
            CourseRecommendation(
                course_id="cuid_course_1",
                title="IELTS Oral Practice Master",
                reason="Based on your 120 seconds speaking practice",
                confidence=0.95
            )
        ]
    )
    mock_model.with_structured_output.return_value = mock_structured_model
    mock_deepseek.return_value = mock_model
    
    # 运行推荐引擎
    res = await generate_recommendations(mock_db, user_id)
    
    assert "recommendations" in res
    assert len(res["recommendations"]) == 1
    assert res["recommendations"][0]["course_id"] == "cuid_course_1"
    assert res["recommendations"][0]["confidence"] == 0.95
    
    # 验证 ClickHouse query 被调用
    mock_ch_client.query.assert_called_once()
    # 验证 PostgreSQL courses 查询被执行
    assert mock_db.execute.call_count >= 1
    # 验证 LangChain structured output 被调用
    mock_model.with_structured_output.assert_called_once()


@pytest.mark.asyncio
@patch("aiosmtplib.send")
@patch("app.llm.embeddings.get_embeddings")
@patch("langchain_chroma.Chroma")
@patch("app.llm.models.create_deepseek")
async def test_nightly_digest_email(mock_deepseek, mock_chroma, mock_embeddings, mock_send):
    """测试每日零点 RAG 错词离线日报生成与异步邮件发送逻辑"""
    from app.services.digest import build_and_send_daily_digest
    
    # Mock Chroma RAG
    mock_vectorstore = MagicMock()
    mock_doc = MagicMock()
    mock_doc.page_content = "Harry Potter had a difficult time learning spells."
    mock_doc.metadata = {"filename": "HarryPotter.txt"}
    mock_vectorstore.similarity_search.return_value = [mock_doc]
    mock_chroma.return_value = mock_vectorstore
    
    # Mock LLM Report Generator
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = MagicMock(content="<html><body>Custom review report</body></html>")
    mock_deepseek.return_value = mock_llm
    
    # Mock DB Session & User
    mock_db = AsyncMock()
    mock_user_result = MagicMock()
    mock_user = MagicMock()
    mock_user.id = "user_id_999"
    mock_user.name = "John Doe"
    mock_user.email = "john@example.com"
    
    # 模拟用户开启了每日定时任务且有今日学词
    mock_user.is_timing_task = True
    mock_user.timing_task_time = "00:00:00"
    mock_user.word_number = 42
    
    mock_user_result.scalars.return_value.all.return_value = [mock_user]
    mock_db.execute.return_value = mock_user_result
    
    # 运行每日日报任务
    # 模拟 get_qualifying_users
    with patch("app.services.digest.get_qualifying_users") as mock_get_users:
        mock_get_users.return_value = [{
            "id": mock_user.id,
            "name": mock_user.name,
            "email": mock_user.email,
            "today_count": 5,
            "mastered_count": 2,
            "word_number": 42,
            "today_words": [{"word": "spell", "translation": "咒语", "is_master": False}]
        }]
        
        success_count = await build_and_send_daily_digest(mock_db)
        
        assert success_count == 1
        mock_send.assert_called_once()
