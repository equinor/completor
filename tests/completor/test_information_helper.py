"""Helper functions for generating Information objects."""

from completor.completion import Information


def test_creation():
    """Test creation of empty Information object."""
    info = Information()
    assert info.num_device is None
    assert info.inner_diameter is None
    assert info.outer_diameter is None
    assert info.annulus_zone is None
    assert info.device_type is None
    assert info.roughness is None
    assert info.annulus_zone is None


def test_simple_initiation():
    """Test initialization of Information object with values."""
    info = Information(
        num_device=1.0,
        device_type="AICD",
        device_number=1,
        inner_diameter=3.0,
        outer_diameter=4.0,
        roughness=0.5,
        annulus_zone=1,
    )
    assert info.num_device == 1.0
    assert info.device_type == "AICD"
    assert info.device_number == 1
    assert info.inner_diameter == 3.0
    assert info.outer_diameter == 4.0
    assert info.roughness == 0.5
    assert info.annulus_zone == 1

    info = Information(
        num_device=[1.0],
        device_type=["AICD"],
        device_number=[1],
        inner_diameter=[3.0],
        outer_diameter=[4.0],
        roughness=[0.5],
        annulus_zone=[1],
    )
    assert info.num_device == [1.0]
    assert info.device_type == ["AICD"]
    assert info.device_number == [1]
    assert info.inner_diameter == [3.0]
    assert info.outer_diameter == [4.0]
    assert info.roughness == [0.5]
    assert info.annulus_zone == [1]


def test_add_empty_information_objects():
    """Test addition on Information object with None-values."""
    info = Information()
    info += Information()
    assert info.num_device == [None]
    assert info.device_type == [None]
    assert info.device_number == [None]
    assert info.inner_diameter == [None]
    assert info.outer_diameter == [None]
    assert info.roughness == [None]
    assert info.annulus_zone == [None]

    info = Information()
    info += Information(
        num_device=1.0,
        device_type="ICD",
        device_number=2,
        inner_diameter=3.0,
        outer_diameter=4.0,
        roughness=3.0,
        annulus_zone=1,
    )

    assert info.num_device == [1.0]
    assert info.device_type == ["ICD"]
    assert info.device_number == [2]
    assert info.inner_diameter == [3.0]
    assert info.outer_diameter == [4.0]
    assert info.roughness == [3.0]
    assert info.annulus_zone == [1]


def test_add_non_empty_information_objects():
    """Test addition on Information object with values."""
    info = Information(
        num_device=3.0,
        device_type="DAR",
        device_number=1,
        inner_diameter=1.0,
        outer_diameter=3.0,
        roughness=1.0,
        annulus_zone=4,
    )
    info += Information(
        num_device=4.2,
        device_type="VALVE",
        device_number=2,
        inner_diameter=2.0,
        outer_diameter=4.0,
        roughness=2.1,
        annulus_zone=2,
    )

    assert info.num_device == [3.0, 4.2]
    assert info.device_type == ["DAR", "VALVE"]
    assert info.device_number == [1, 2]
    assert info.inner_diameter == [1.0, 2.0]
    assert info.outer_diameter == [3.0, 4.0]
    assert info.roughness == [1.0, 2.1]
    assert info.annulus_zone == [4, 2]
