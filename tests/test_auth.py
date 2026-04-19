async def test_register_success(client):
    response = await client.post(
        "/auth/register",
        json={"email": "newuser@gmail.com", "password": "12345678"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@gmail.com"
    assert data["id"] is not None
    assert data["is_confirmed"] == False


async def test_register_duplicate_user(client, test_user):
    response = await client.post(
        "/auth/register",
        json={"email": test_user["email"], "password": "12345678"}
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


async def test_login_success(client, confirmed_user, db_session):
    response = await client.post(
        "/auth/login",
        json=confirmed_user,
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_unconfirmed_email(client, test_user):
    response = await client.post(
        "/auth/login",
        json=test_user
    )

    assert response.status_code == 404
    assert "User is not confirmed" in response.json()["detail"]


async def test_login_incorrect_data(client, confirmed_user, db_session):

    response = await client.post(
        "/auth/login",
        json={"email": confirmed_user["email"], "password": "12345677" }
    )

    assert response.status_code == 401
    assert "Email or password incorrect" in response.json()["detail"]





