import os
import logging


class Logger:

    _logger = None

    @classmethod
    def logger(cls, context) -> logging.Logger:

        if cls._logger is not None:
            return cls._logger

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(process)d - %(thread)d - %(levelname)s - %(filename)s - %(message)s')

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(context.log_level)
        stream_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(os.path.join(context.run_path, "run.runner.log"))
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        cls._logger = logging.getLogger("pymergen")
        cls._logger.setLevel(logging.DEBUG)
        cls._logger.addHandler(stream_handler)
        cls._logger.addHandler(file_handler)

        return cls._logger
