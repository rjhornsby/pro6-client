from enum import Enum


class Status(Enum):
    OFFLINE = 0  # ProPresenter not reachable
    STANDBY = 1  # Connected to ProPresenter, but no slide data
    ACTIVE = 2   # Connected to ProPresenter, with slide data
