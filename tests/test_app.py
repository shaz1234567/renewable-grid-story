def test_app_exports_wsgi_server_and_six_views():
    import app

    assert app.server is app.app.server
    section_ids = {
        component.id
        for component in app.app.layout._traverse()
        if getattr(component, "id", None)
        and str(component.id) in {f"view-{number}" for number in range(1, 7)}
    }
    assert section_ids == {f"view-{number}" for number in range(1, 7)}


def test_required_source_period_and_takeaway_controls_exist():
    import app

    ids = {
        component.id
        for component in app.app.layout._traverse()
        if getattr(component, "id", None)
    }
    assert {
        "v4-source",
        "v5-dates",
        "v6-dates",
        "v1-takeaway",
        "v4-takeaway",
        "v5-takeaway",
        "v6-takeaway",
    } <= ids
