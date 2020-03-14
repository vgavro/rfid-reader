from .ind903_reader.ind903_reader import Ind903Reader


PROTOCOL_REGISTRY = {
    'ind903': Ind903Reader,
    'yr903': Ind903Reader,
    'yr904': Ind903Reader,
}


def create_socket(address, family=-1, socket_type=-1, proto=-1, fileno=None,
                  connect_timeout=None, timeout=None):
    import socket

    if isinstance(family, str):
        family = getattr(socket, f'AF_{family.upper()}')
    if isinstance(socket_type, str):
        socket_type = getattr(socket, f'SOCK_{socket_type.upper()}')

    channel = socket.socket(family, socket_type, proto, fileno)
    if connect_timeout is not None:
        channel.settimeout(connect_timeout)
    try:
        channel.connect(tuple(address) if isinstance(address, list) else address)
    except Exception:
        channel.close()
        raise
    channel.settimeout(timeout)
    return channel


def create_tcp(host, port, **kwargs):
    import socket

    return create_socket((host, port), socket.AF_INET, socket.SOCK_STREAM,
                         **kwargs)


def create_serial(port, baudrate=115200, **kwargs):
    # '/dev/ttyUSB0'
    import serial  # pip install pyserial

    rv = serial.Serial(port, baudrate, **kwargs)
    if rv is None:
        # Not sure it can be None instead of raising exception,
        # maybe some magic with metaclass, but leave it as it was in old code
        raise RuntimeError('No device found, please check the port name '
                           '(i.e., python -m serial.tools.list_ports)')
    return rv


CHANNEL_REGISTRY = {
    'socket': create_socket,
    'tcp': create_tcp,
    'serial': create_serial,
}


def create_channel(channel_type, **kwargs):
    try:
        channel_cls = CHANNEL_REGISTRY[channel_type]
    except KeyError:
        raise ValueError(f'Unknown channel {channel_type}, '
                         f'choices are {tuple(CHANNEL_REGISTRY)}')
    return channel_cls(**kwargs)


def create_reader(protocol, channel, **kwargs):
    try:
        reader_cls = PROTOCOL_REGISTRY[protocol]
    except KeyError:
        raise ValueError(f'Unknown protocol {protocol}, '
                         f'choices are {tuple(PROTOCOL_REGISTRY)}')
    return reader_cls(channel, **kwargs)
