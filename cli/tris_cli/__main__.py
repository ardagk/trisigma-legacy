from trisigma import command
import tris_cli.builtins
import sys

@command.expose()
def hello():
    print('Hello, world!')

if __name__ == '__main__':
    #parse args, first arg is the command rest are args
    #line_s = " ".join(sys.argv[1:])
    resp = command.execute(sys.argv[1:])
    if resp: print(resp)
    pass
