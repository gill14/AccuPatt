from accupatt.models.OptBase import OptBase


class PassDataBase(OptBase):
    def __init__(self, name):
        super().__init__(name=name)
        self.include_in_composite = True

    def has_data() -> bool:
        # MUST override in inherited class
        pass
