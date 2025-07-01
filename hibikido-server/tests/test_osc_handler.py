from hibikido.osc_handler import OSCHandler


def test_parse_args_basic():
    args = OSCHandler.parse_args("hello", 42, None, "extra")
    assert args["arg1"] == "hello"
    assert args["arg2"] == "42"
    assert args["arg3"] == ""
    assert args["arg4"] == "extra"


def test_parse_args_segment_style():
    args = OSCHandler.parse_args(
        "sounds/wind/forest.wav",
        "description",
        "wind gusts",
        "start",
        0.1,
        "end",
        0.6,
    )
    assert args["arg1"] == "sounds/wind/forest.wav"
    assert args["arg2"] == "description"
    assert args["arg3"] == "wind gusts"
    assert args["arg4"] == "start"
    assert args["arg5"] == "0.1"
    assert args["arg6"] == "end"
    assert args["arg7"] == "0.6"
