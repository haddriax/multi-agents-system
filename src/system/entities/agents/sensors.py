class Sensor:
    """
    Represent a way to perceive the environnement.
    For now, we only have an optical sensor, but we could add more like radiation sensor,
    so this class force the design to work with n named sensors.
    """
    def __init__(self, radius: int = 6) -> None:
        self.radius = radius


class OpticalSensor(Sensor):
    """
    The most basic and principal sensor.
    """
    def __init__(self, radius: int = 3) -> None:
        super().__init__(radius)
