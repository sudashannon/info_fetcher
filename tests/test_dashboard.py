import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.item import Item
from app.db.database import SessionLocal, Base, engine

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    """为每个测试函数提供一个干净的数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.query(Item).delete() # 清理数据
        db.commit()
        db.close()

def test_view_dashboard_no_data(db_session):
    """测试数据库为空时访问后台页面"""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers['content-type']
    assert "暂无数据" in response.text

def test_view_dashboard_with_data(db_session):
    """测试数据库有数据时访问后台页面"""
    # 准备测试数据
    test_item = Item(title="一个测试标题", url="http://example.com", source="测试来源")
    db_session.add(test_item)
    db_session.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers['content-type']
    # 验证测试数据是否出现在页面上
    assert "一个测试标题" in response.text
    assert "http://example.com" in response.text
    assert "测试来源" in response.text
