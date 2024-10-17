from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from functools import cached_property


@dataclass
class SerializableDataclass:
    def serialize(self):
        return asdict(self)


@dataclass
class HidData(SerializableDataclass):
    hex: str
    expect_answer: bool = True
    answer_report_id: int | None = None
    """if not provided, the default `answer_report_id` of the wheelbase definition is used"""


@dataclass
class WheelbaseConfiguration(SerializableDataclass, ABC):
    high_torque_enabled: bool
    profile_id: int
    profile_name: str | None = None

    @classmethod
    def from_hid_hex_data(cls, hid_hex_data: str):
        # hid_hex_data should be 61 byte, therefore 122 chars
        assert len(hid_hex_data) == 122, f'Unknown data format for {cls.__name__} - should be exactly 61 bytes long. Maybe firmware changed the format?'
        return cls(
            profile_id=int(hid_hex_data[36:38], base=16),  # byte 19, profile index
            high_torque_enabled=hid_hex_data[108:110] == '04',  # byte 55, disabled: 00, enabled: 04
        )

    def parse_profile_name_hid_hex_data(self, hid_hex_data: str):
        found_data = False
        concated_hex = ''
        for byte_index in range(4, len(hid_hex_data), 2):
            hex = hid_hex_data[byte_index:byte_index + 2]
            if hex == '00':
                if found_data:
                    break
                continue
            found_data = True
            concated_hex += hex
        self.profile_name = bytes.fromhex(concated_hex).decode()

    def serialize(self):
        return asdict(self)


@dataclass
class WheelbaseDefinition(SerializableDataclass, ABC):
    name: str
    product_id: int
    configuration_class: type[WheelbaseConfiguration]
    send_report_id: int
    answer_report_id: int
    get_configuration_hid_data: HidData
    enable_high_torque_hid_data: list[HidData]
    disable_high_torque_hid_data: list[HidData]
    get_profile_name_hid_data: HidData
    set_profile_hid_data: HidData
    """Should take a placeholder `profile_id`"""
    vendor_id: int = 0x2433

    @staticmethod
    def as_hex_str(value: int) -> str:
        return hex(value)[2:]  # strip 0x

    @cached_property
    def vendor_id_hex(self):
        return self.as_hex_str(self.vendor_id)

    @cached_property
    def product_id_hex(self):
        return self.as_hex_str(self.product_id)

    @cached_property
    def send_report_id_hex(self):
        return self.as_hex_str(self.send_report_id)

    @cached_property
    def answer_report_id_hex(self):
        return self.as_hex_str(self.answer_report_id)

    def __str__(self):
        return self.name
