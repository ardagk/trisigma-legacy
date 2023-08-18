from trisigma import command

@command.expose()
def tail(path='/var/log/trisigma.log', ssh=None):
    """tail logs"""
    import os
    if not ssh:
        os.system(f'tail -f {path}')
    else:
        os.system(f'ssh {ssh} "tail -f {path}"')

