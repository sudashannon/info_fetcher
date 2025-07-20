from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """测试根路径是否能正常访问"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "欢迎使用实时热点聚合与推送系统"}
