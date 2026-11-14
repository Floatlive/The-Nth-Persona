import json

from server import main


def test_state_recovers_invalid_version_without_reusing_history(monkeypatch, tmp_path):
    current_file = tmp_path / "current.json"
    history_file = tmp_path / "history.json"
    current_file.write_text(
        json.dumps(
            {
                "user_id": "default",
                "persona": "sharp-advisor",
                "name": "旧名称",
                "switched_at": "2026-01-01T00:00:00+00:00",
                "version": "broken",
            }
        ),
        encoding="utf-8",
    )
    history_file.write_text(
        json.dumps([{"persona": "cold-executor", "name": "冷酷执行官", "version": 7}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "DATA_FILE", current_file)
    monkeypatch.setattr(main, "HISTORY_FILE", history_file)

    state = main.read_current()

    assert state["persona"] == "sharp-advisor"
    assert state["name"] == "现实毒舌顾问"
    assert state["version"] == 8
    assert json.loads(current_file.read_text(encoding="utf-8"))["version"] == 8


def test_reset_advances_persona_version(monkeypatch, tmp_path):
    current_file = tmp_path / "current.json"
    history_file = tmp_path / "history.json"
    monkeypatch.setattr(main, "DATA_FILE", current_file)
    monkeypatch.setattr(main, "HISTORY_FILE", history_file)

    switched = {
        **main._default_state(),
        "persona": "minimalist",
        "name": "极简主义者",
        "version": 4,
        "previous": "cold-executor",
    }
    main._atomic_write_json(current_file, switched)

    result = main.reset()
    history = json.loads(history_file.read_text(encoding="utf-8"))

    assert result["current"]["persona"] == "cold-executor"
    assert result["current"]["version"] == 5
    assert history[-1]["version"] == 5
