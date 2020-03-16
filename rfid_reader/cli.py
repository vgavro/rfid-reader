import time
import os.path

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


HELP = """Example config file (yaml)

```

{config}
```
""".format(config=(
        open(os.path.join(os.path.dirname(__file__),
                          'rfid-reader.example.conf')).read()
        # all this shit because of click parahraph reformatting rules
        .replace('##\n', '\b\n')
))


@click.command(help=HELP)
@click.option('-c', '--config', default='rfid-reader.conf', type=click.File('r'))
def rfid_reader(config):
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
