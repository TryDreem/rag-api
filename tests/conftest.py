import asyncio
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared"


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Creating engine and tables only once for all tests"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,
        poolclass=StaticPool,
        connect_args={"uri": True}
    )
    #open a connection and start a transaction
    async with engine.begin() as conn:
        # create all tables defined in Base.metadata
        # run_sync is needed because create_all is synchronous
        await conn.run_sync(Base.metadata.create_all)

    #provide engine to tests
    yield engine

    #open connection again
    async with engine.begin() as conn:
        #drop all tables (clean up database after tests)
        await conn.run_sync(Base.metadata.drop_all)
    #fully close engine and all connections
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    # close the session
    await session.close()
    # rollback all changes made during the test
    # this ensures database state is clean for the next test
    await transaction.rollback()
    # close the connection
    await connection.close()

@pytest_asyncio.fixture(autouse=True)  # automatically applied to all tests
async def mock_external():
    # patch external dependencies to avoid real API calls

    with patch(
            "app.core.embeddings.get_embedding",
            return_value=[0.1] * 384  # mock embedding vector (fixed size list)
    ), \
            patch(
                "app.services.chat_service.client"  # mock the external client (e.g. LLM API)
            ) as mock_groq:

        # mock async method for chat completion
        mock_groq.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                # simulate API response structure
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="test answer"  # fake response from model
                        )
                    )
                ]
            )
        )

        # provide mocked environment to tests
        yield


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    #pytest will use override_get_db instead of get_db
    app.dependency_overrides[get_db] = override_get_db
    #asgi for httpx to work without starting app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(client):
    user_data = {
        "email": "test@gmail.com",
        "password": "12345678"
    }

    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    return user_data


@pytest_asyncio.fixture
async def auth_headers(client, test_user,db_session):
    from app.models.user import User
    from sqlalchemy import update

    query = update(User).where(User.email == test_user["email"]).values(is_confirmed=True)
    await db_session.execute(query)
    await db_session.commit()

    response = await client.post("auth/login", json=test_user)
    assert response.status_code == 200
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
