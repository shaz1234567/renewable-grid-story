from src.callbacks import playback_reset, playback_step, source_selection


def test_playback_clamps_at_boundaries():
    assert playback_step(0, -1, 23) == 0
    assert playback_step(23, 1, 23) == 23
    assert playback_step(8, 1, 23) == 9
    assert playback_reset(23) == 0


def test_source_selection_filters_unknowns_and_resets():
    assert source_selection(None, ["solar_mw", "not_a_source"]) == ["solar_mw"]
    assert source_selection("v6-reset", []) == ["solar_mw", "wind_mw", "hydro_mw"]
