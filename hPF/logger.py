import sys
import logging
from mpi4py import MPI


class MPIFilter(logging.Filter):
    def filter(self, record):
        if MPI.COMM_WORLD.Get_rank() == 0:
            return True
        else:
            return False


class Logger:
    level = None
    log_file = None
    format = '%(levelname)-8s [%(filename)s:%(lineno)d] <%(funcName)s> %(message)s'  # noqa: E501
    date_format = '%(asctime)s,%(msecs)d'
    formatter = logging.Formatter(fmt=date_format + format)
    rank0 = logging.getLogger('HyMD.rank_0')
    all_ranks = logging.getLogger('HyMD.all_ranks')

    @classmethod
    def setup(cls, default_level=logging.INFO, log_file=None,
              log_to_stdout=False):
        cls.level = default_level
        cls.log_file = log_file

        cls.rank0.setLevel(default_level)
        cls.all_ranks.setLevel(default_level)

        cls.rank0.addFilter(MPIFilter())

        if (not log_file) and (not log_to_stdout):
            return
        if log_file:
            cls.log_file_handler = logging.FileHandler(log_file)
            cls.log_file_handler.setLevel(default_level)
            cls.log_file_handler.setFormatter(cls.formatter)

            cls.rank0.addHandler(cls.log_file_handler)
            cls.all_ranks.addHandler(cls.log_file_handler)

        if log_to_stdout:
            cls.log_to_stdout = True
            cls.stdout_handler = logging.StreamHandler()
            cls.stdout_handler.setLevel(default_level)
            cls.stdout_handler.setStream(sys.stdout)
            cls.stdout_handler.setFormatter(cls.formatter)

            cls.rank0.addHandler(cls.stdout_handler)
            cls.all_ranks.addHandler(cls.stdout_handler)
