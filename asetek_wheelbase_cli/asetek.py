import logging
import usb.util

from asetek_wheelbase_cli.wheelbases import HidData, WheelbaseDefinition, WHEELBASE_DEFINITIONS
from dataclasses import dataclass
from time import sleep
from typing import Iterable
from usb.core import Configuration, Device, Endpoint, Interface, USBError


class ReportWaitTimeout(Exception):
    ...


@dataclass
class AsetekWheelbase:
    """
    Common USB interaction class for asetek wheelbases

    Searches USB devices for known wheelbases and uses first found

    Not designed to be used without contextmanager
    """
    definition: WheelbaseDefinition | None = None
    device: Device = None
    configuration: Configuration = None
    interface: Interface = None
    endpoint_in: Endpoint = None
    endpoint_out: Endpoint = None

    def _setup(self):
        if self.device is not None:
            # already set up
            return

        for definition in WHEELBASE_DEFINITIONS:
            if device := usb.core.find(idVendor=definition.vendor_id, idProduct=definition.product_id):
                self.definition = definition
                self.device = device
                logging.info(f'Found wheelbase {definition}')
                break

        assert self.device, 'No wheelbase found'

        self.configuration = self.device.get_active_configuration()
        if self.configuration is None:
            logging.debug('Activating default configuration')
            self.device.set_configuration()
            self.configuration = self.device.get_active_configuration()
        logging.debug(f'Using configuration {self.configuration.index}')

        self.interface = usb.util.find_descriptor(self.configuration, bInterfaceClass=3)
        assert self.interface, 'No interface found in active configuration'
        if self.device.is_kernel_driver_active(self.interface.index):
            logging.debug('Detaching interface from kernel driver')
            try:
                self.device.detach_kernel_driver(self.interface.index)
            except USBError as e:
                logging.error(f'Error while detatching kernel driver from interface {self.interface.index}: {e}')
                exit(1)

        logging.debug(f'Using interface {self.interface.index}')
        usb.util.claim_interface(self.device, interface=self.interface.index)

        self.endpoint_in = usb.util.find_descriptor(
            self.interface,
            # match the first IN endpoint
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        )
        assert self.endpoint_in, 'No in endpoint found'
        logging.debug(f'Using in endpoint {self.endpoint_in.index}')

        self.endpoint_out = usb.util.find_descriptor(
            self.interface,
            # match the first OUT endpoint
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )
        assert self.endpoint_out, 'No out endpoint found'
        logging.debug(f'Using out endpoint {self.endpoint_out.index}')

    def _cleanup(self):
        if self.device:
            usb.util.dispose_resources(self.device)

    def __enter__(self):
        self._setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._cleanup()

    def read_data(self, length: int = 64) -> str:
        """
        returns read hex data
        """
        hex_data = self.endpoint_in.read(length).tobytes().hex()
        logging.debug(f'Received data: {hex_data}')
        return hex_data

    def send_data(self, hex_data: str):
        logging.debug(f'Sending data: {hex_data}')
        self.endpoint_out.write(bytes.fromhex(hex_data))
        sleep(0.2)

    def read_hid_report(self, hid_hex_report_id: str | None = None, max_tries: int = 30):
        """
        hid_hex_report_id -- if omitted, will use `answer_report_id` from wheelbase definition

        max_tries -- maximum packets to wait for desired report id until `ReportWaitTimeout` is raised
        """
        if hid_hex_report_id is None:
            hid_hex_report_id = self.definition.answer_report_id_hex

        hex_data: str | None = None
        tries = 0
        while hex_data is None or hex_data[0:2] != hid_hex_report_id:
            hex_data = self.read_data()
            tries += 1
            if tries % 10 == 0:
                logging.debug(f'Still waiting for report of id {hid_hex_report_id}')
            if tries >= max_tries:
                raise ReportWaitTimeout(f'No report of id {hid_hex_report_id} received in the last {tries} packets')
        return hex_data

    def send_hid_report(self, hid_hex_data: str, hid_hex_report_id: str = None):
        """
        hid_hex_data -- only hid data without leading report id

        hid_hex_report_id -- if omitted, will use `send_report_id` from wheelbase definition as prefix to hid_hex_data
        """
        if hid_hex_report_id is None:
            hid_hex_report_id = self.definition.send_report_id_hex
        self.send_data(hid_hex_report_id + hid_hex_data)

    def send_hid_data(self, hid_data: HidData | list[HidData]):
        """
        hid_data -- data definition(s) to send and respect
        """
        data_list = hid_data if isinstance(hid_data, Iterable) else [hid_data]
        for hid_data in data_list:
            self.send_hid_report(hid_hex_data=hid_data.hex)
            if hid_data.expect_answer:
                self.read_hid_report(hid_hex_report_id=hid_data.answer_report_id)

    def get_current_configuration(self):
        """
        uses wheelbase definition `get_configuration_hid_data` to read current configuration
        """
        hid_data = self.definition.get_configuration_hid_data
        self.send_hid_report(hid_hex_data=hid_data.hex)
        hid_hex_data = self.read_hid_report(hid_hex_report_id=hid_data.answer_report_id)

        config = self.definition.configuration_class.from_hid_hex_data(hid_hex_data=hid_hex_data)

        if self.definition.get_profile_name_hid_data:
            hid_data = self.definition.get_profile_name_hid_data
            self.send_hid_report(
                hid_hex_data=hid_data.hex.format(
                    profile_id=config.profile_id
                )
            )
            hid_hex_data = self.read_hid_report(hid_hex_report_id=hid_data.answer_report_id)
            config.parse_profile_name_hid_hex_data(hid_hex_data=hid_hex_data)

        return config
