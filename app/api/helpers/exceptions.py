class SuppliedDataException(Exception):
  def __init__(self, msg=None,) -> None:
    super().__init__()
    self.msg = msg