import json
import logging
import os

from asetek_wheelbase_cli.asetek import AsetekWheelbase
from asetek_wheelbase_cli.wheelbases import HidData
from typer import Argument, Exit, Option, Typer


cli = Typer()
set_cli = Typer(name='set')
cli.add_typer(set_cli)


@cli.callback()
def main(
    verbosity: int = Option(0, '-v', help='Increases verbosity', count=True)
):
    log_level = logging.INFO
    if verbosity >= 1:
        log_level = logging.DEBUG
    if verbosity >= 2:
        os.environ['LIBUSB_DEBUG'] = '4'
        os.environ['PYUSB_DEBUG'] = 'debug'
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)-8s %(message)s ',
        datefmt='%Y-%m-%dT%H:%M:%SZ',
        force=True
    )


@cli.command()
def test():
    """Tests readonly connectivity and setup"""
    with AsetekWheelbase() as wheelbase:
        wheelbase.read_data()
        logging.info('Successful read data from device')  # otherwise an exception is thrown
        configuration = wheelbase.get_current_configuration()
        logging.info(f'Successfully read configuration: {configuration}')


@cli.command()
def config():
    """Prints configuration"""
    with AsetekWheelbase() as wheelbase:
        configuration = wheelbase.get_current_configuration()
        print(json.dumps(configuration.serialize(), indent=4))


@set_cli.command()
def high_torque(enabled: bool = Argument(help='If high torque should be enabled')):
    with AsetekWheelbase() as wheelbase:
        verb = 'enabled' if enabled else 'disabled'
        configuration = wheelbase.get_current_configuration()
        if enabled == configuration.high_torque_enabled:
            logging.info(f'High Torque is already {verb}')
            return

        wheelbase.send_hid_data(
            wheelbase.definition.enable_high_torque_hid_data if enabled else wheelbase.definition.disable_high_torque_hid_data
        )

        configuration = wheelbase.get_current_configuration()
        if enabled != configuration.high_torque_enabled:
            logging.error(f'High Torque did not change and is not {verb}')
            raise Exit(1)
        logging.info(f'High Torque successfully {verb}')


@set_cli.command()
def profile(profile_id: int = Argument(help='Id of the profile - zero indexed (top item in RaceHub is Id 0)')):
    with AsetekWheelbase() as wheelbase:
        configuration = wheelbase.get_current_configuration()
        if configuration.profile_id == profile_id:
            logging.info(f'Profile {profile_id} is already active')
            return

        hid_data = HidData(**wheelbase.definition.set_profile_hid_data.serialize())
        hid_data.hex = hid_data.hex.format(profile_id=profile_id)
        wheelbase.send_hid_data(hid_data)

        configuration = wheelbase.get_current_configuration()
        if configuration.profile_id != profile_id:
            logging.error(f'Profile did not change - maybe id {profile_id} is not setup yet?')
            raise Exit(1)
        logging.info(f'Profile {profile_id} is now active')


if __name__ == "__main__":
    cli()
