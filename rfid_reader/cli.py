import time

import click
import yaml
import structlog

from . import create_channel, create_reader


logger = structlog.get_logger()


def do_inventory_forever(channel_factory, reader_factory, retry_timeout=None):
    while True:
        try:
            channel = channel_factory()
        except (ConnectionError, OSError, IOError, RuntimeError) as exc:
            logger.error('Channel create error', error=exc, sleep=retry_timeout)
            if retry_timeout is None:
                raise
            time.sleep(retry_timeout)
            continue

        reader = reader_factory(channel)

        try:
            reader.do_inventory(lambda epc: logger.info('Found', epc=epc))
        except (ConnectionError, OSError, IOError, RuntimeError) as exc:
            logger.error('Inventory loop error', error=exc, sleep=retry_timeout)
            if retry_timeout is None:
                raise
        finally:
            channel.close()
        time.sleep(retry_timeout)


@click.command()
@click.option('-c', '--config', default='rfid-reader.conf', type=click.File('r'))
def rfid_reader(config):
    """Example config file (yaml)

    \b
    ```
    reader:
        type: yr904
        wait_timeout: 0.2  # seconds, default read wait
        trace: true  # if set to true we get each packet send/recv (MUCH information)

    \b
    channel:
        type: tcp
        host: 192.168.0.178
        port: 4001
        connect_timeout: 3  # seconds
        # https://docs.python.org/3/library/socket.html#socket.socket.settimeout
        # timeout: 5  # read(?) timeout, not sure how it's work with current logic

    \b
    # socket example ("tcp" is shortcut for INET, STREAM, address=(host, port))
    # see https://docs.python.org/3/library/socket.html#socket.socket
    # channel:
    #     type: socket
    #     family: INET  # or INET6
    #     socket_type: STREAM  # STREAM for tcp, DGRAM for udp
    #     address: ['192.168.0.178', 4001]


    \b
    # serial example (pyserial module required)
    # see https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial
    # channel:
    #     type: serial
    #     port: /dev/ttyUSB0
    #     baudrate: 115200

    \b
    retry_timeout: 1  # seconds, if null - exit on first fail
    ```
    """
    config = yaml.safe_load(config)

    channel_opts = config.pop('channel')
    channel_type = channel_opts.pop('type')

    reader_opts = config.pop('reader')
    reader_type = reader_opts.pop('type')

    if reader_opts.pop('trace', False):
        reader_opts['trace'] = lambda msg: logger.debug('trace', trace=msg)
    else:
        reader_opts['trace'] = lambda msg: msg

    do_inventory_forever(
        lambda: create_channel(channel_type, **channel_opts),
        lambda channel: create_reader(reader_type, channel, **reader_opts),
        retry_timeout=config.pop('retry_timeout', None)
    )
