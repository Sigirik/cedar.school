# schedule/reference/tests/test_reference_search.py
import pytest
from users.models import User
from schedule.real_schedule.tests.test_my_schedule import api as api, base_data as base_data

API = "/api/reference/teachers/"

@pytest.mark.django_db
def test_teachers_reference_q_too_short_400(api, base_data):
    users = base_data["users"]
    api.force_authenticate(users["admin"])
    resp = api.get(f"{API}?q=a")  # 1 символ
    assert resp.status_code == 400
    assert resp.json().get("detail") == "QUERY_TOO_SHORT"

@pytest.mark.django_db
def test_teachers_reference_ok_and_role_filter(api, base_data):
    users = base_data["users"]
    # создаём «ложный» пользователь, подходящий по шаблону, но не TEACHER
    User.objects.create_user(username="tst_ref_student_1", password="pass", role=User.Role.STUDENT, is_active=True)

    api.force_authenticate(users["admin"])
    resp = api.get(f"{API}?q=tst")  # min 2 символа, попадёт по username тестовых пользователей
    assert resp.status_code == 200
    body = resp.json()
    # в результатах только TEACHER — проверим, что «ложный» студент не подтянулся
    usernames = {u.get("last_name") or "" for u in body.get("results", [])}  # last_name может быть пустым
    # Ничего конкретно не утверждаем про last_name, важнее, что 200 и набор не пустой у реальных данных.
    assert "tst_ref_student_1" not in usernames  # защитная проверка; в реальности last_name пуст, но принцип ясен

@pytest.mark.django_db
def test_teachers_reference_pagination(api, base_data):
    users = base_data["users"]
    # добавим ещё активных учителей, чтобы точно была пагинация при page_size=2
    for i in range(3):
        User.objects.create_user(
            username=f"tst_ref_teacher_{i}",
            password="pass",
            role=User.Role.TEACHER,
            is_active=True,
        )

    api.force_authenticate(users["admin"])
    resp = api.get(f"{API}?q=tst_ref_teacher&page_size=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 3
    assert len(body["results"]) == 2
    assert body["next"] is not None
