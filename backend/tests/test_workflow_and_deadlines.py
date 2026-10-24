def test_deficiency_guard_and_cure_loop(client):
    # 1. Log in as Regional Officer
    login_ro = client.post("/api/auth/login", json={
        "email": "ro.western@aicte.gov.in",
        "password": "Password123!"
    }).json()
    ro_token = login_ro["access_token"]

    # 2. Log in as Apex Admin
    login_apex = client.post("/api/auth/login", json={
        "email": "admin@apex.edu.in",
        "password": "Password123!"
    }).json()
    apex_token = login_apex["access_token"]

    # Find Apex EOA app
    apps = client.get("/api/applications", headers={"Authorization": f"Bearer {apex_token}"}).json()
    app = next(a for a in apps if a["application_number"] == "AICTE-2026-EOA-98124")

    # Verify transition to SCRUTINY_COMPLETED fails while open deficiencies exist
    res_fail = client.post(
        f"/api/applications/{app['id']}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "SCRUTINY_COMPLETED", "remarks": "Attempting signoff with open deficiency"}
    )
    assert res_fail.status_code in [400, 403]

    # Institution cures open deficiencies
    detail = client.get(f"/api/applications/{app['id']}", headers={"Authorization": f"Bearer {apex_token}"}).json()
    for def_item in detail["deficiencies"]:
        if def_item["status"] == "OPEN":
            res_cure = client.post(
                f"/api/applications/{app['id']}/cure-deficiency/{def_item['id']}",
                headers={"Authorization": f"Bearer {apex_token}"},
                json={"cure_remarks": "Rectified as per AICTE norms", "cure_document_url": "/api/documents/download/cure.pdf"}
            )
            assert res_cure.status_code == 200

    # Resubmit application
    res_resubmit = client.post(
        f"/api/applications/{app['id']}/transition",
        headers={"Authorization": f"Bearer {apex_token}"},
        json={"to_stage": "RESUBMITTED", "remarks": "Deficiencies cured"}
    )
    assert res_resubmit.status_code == 200

    # Officer marks deficiencies as resolved
    for def_item in detail["deficiencies"]:
        client.post(
            f"/api/applications/{app['id']}/resolve-deficiency/{def_item['id']}",
            headers={"Authorization": f"Bearer {ro_token}"}
        )

    # Officer advances to UNDER_SCRUTINY and then to SCRUTINY_COMPLETED
    client.post(
        f"/api/applications/{app['id']}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "UNDER_SCRUTINY", "remarks": "Re-scrutiny"}
    )
    res_complete = client.post(
        f"/api/applications/{app['id']}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"to_stage": "SCRUTINY_COMPLETED", "remarks": "All cured and verified"}
    )
    assert res_complete.status_code == 200
    assert res_complete.json()["current_stage"] == "SCRUTINY_COMPLETED"

def test_deadline_scanner_idempotency(client):
    login_admin = client.post("/api/auth/login", json={
        "email": "sysadmin@aicte.gov.in",
        "password": "Password123!"
    }).json()
    token = login_admin["access_token"]

    # First run
    res1 = client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 200
    data1 = res1.json()

    # Second run immediately after
    res2 = client.post("/api/alerts/run-scan", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    data2 = res2.json()

    # Second run must not create duplicate reminders or escalations
    assert data2["reminders_created"] == 0
    assert data2["escalations_created"] == 0
    assert data2["duplicates_prevented"] >= data1["escalations_created"]
