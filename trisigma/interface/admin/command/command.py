import argparse

class Command ():
    def __init__(self, func, args, kwargs):
        self.name = func.__name__
        self.func = func

        self.__seperator = len(args)
        self.__parser = argparse.ArgumentParser()
        for arg in args:
            self.__parser.add_argument(arg)
        for k, v in kwargs.items():
            if isinstance(v, bool):
                # if boolean, default to false add a flag
                self.__parser.add_argument("--" + k, action="store_true")
                #self.__parser.add_argument("--" + k, default=v, action=f"store_{str(not v).lower()}")
            else:
                self.__parser.add_argument("--" + k, default=v)
        self.parse_error = []
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def parse(self, argv):
        try:
            parsed_args, err = self.__parser.parse_known_args(argv)
            if err:
                msg = "unrecognized arguments: %s" % " ".join(err)
                raise argparse.ArgumentError(None, msg)

            parsed_args_dict = vars(parsed_args)
            for k, v in parsed_args_dict.items():
                try:
                    parsed_args_dict[k] = float(v)
                    parsed_args_dict[k] = int(v)
                except (ValueError, TypeError):
                    pass

            args = tuple(parsed_args_dict.values())[:self.__seperator]
            kwargs = {k: v for k, v in parsed_args_dict.items() if v not in args}
            return args, kwargs
        except SystemExit:
            msg = self.__parser.format_help()
            raise ValueError(msg)
        except argparse.ArgumentError as e:
            msg =  e.message + "\n" + self.__parser.format_help()
            raise ValueError(msg)


