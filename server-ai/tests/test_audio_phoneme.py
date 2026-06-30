import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_pronunciation_phoneme_evaluation():
    """测试音素级口语纠音评测算法，比对 allowance 与 allowins"""
    from app.services.audio import evaluate_pronunciation
    
    standard_word = "allowance"
    user_spoke = "allowins"
    
    report = evaluate_pronunciation(standard_word, user_spoke)
    
    assert "score" in report
    assert "details" in report
    assert isinstance(report["score"], int)
    assert 0 <= report["score"] <= 100
    
    details = report["details"]
    assert len(details) > 0
    
    # 查找是否有标记为 mispronounced (错读) 的音素/字符
    mispronounced = [d for d in details if d["status"] == "mispronounced"]
    assert len(mispronounced) > 0
    
    print(f"\n评分报告: 分数={report['score']}, 详情={report['details']}")


@pytest.mark.asyncio
@patch("app.socketio.sio")
@patch("app.services.audio.transcribe_audio")
async def test_socketio_audio_events(mock_transcribe, mock_sio):
    """测试 Socket.IO 事件：收集二进制切片并在接收到结束事件时执行 ASR 和纠音"""
    from app.socketio import handle_audio_chunk, handle_audio_end, audio_buffers
    
    sid = "test_socket_session_id"
    mock_transcribe.return_value = "allowins"
    
    # 模拟 sio.emit 为 AsyncMock
    mock_sio.emit = AsyncMock()
    
    # 清理已存在的 buffer
    if sid in audio_buffers:
        del audio_buffers[sid]
        
    # 模拟流式上传 2 个 binary chunk
    await handle_audio_chunk(sid, b"Audio chunk 1 ")
    await handle_audio_chunk(sid, b"Audio chunk 2")
    
    # 验证 buffer 是否正确累加
    assert sid in audio_buffers
    assert audio_buffers[sid].getvalue() == b"Audio chunk 1 Audio chunk 2"
    
    # 触发结束事件并进行评测
    await handle_audio_end(sid, {"targetWord": "allowance"})
    
    # 验证缓冲已从 session 中移除并释放
    assert sid not in audio_buffers
    
    # 验证 ASR 驱动被正确执行
    mock_transcribe.assert_called_once_with(b"Audio chunk 1 Audio chunk 2")
    
    # 验证 Socket.IO 向客户端 room 回传了识别结果和评分
    mock_sio.emit.assert_called_once()
    call_args = mock_sio.emit.call_args
    event_name = call_args[0][0]
    payload = call_args[0][1]
    room_param = call_args[1].get("room")
    
    assert event_name == "audio_transcribed"
    assert room_param == sid
    assert payload["text"] == "allowins"
    assert "evaluation" in payload
    assert payload["evaluation"]["score"] in (50, 66)
