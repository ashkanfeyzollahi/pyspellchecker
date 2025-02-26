""" Additional utility functions """
import contextlib
import functools
import gzip
import re
import typing
import warnings
from pathlib import Path

from spellchecker.info import __version__

KeyT = typing.Union[str, bytes]
PathOrStr = typing.Union[Path, str]


def fail_after(version: str) -> typing.Callable:
    """Decorator to add to tests to ensure that they fail if a deprecated
    feature is not removed before the specified version

    Args:
        version (str): The version to check against"""

    def decorator_wrapper(func):
        @functools.wraps(func)
        def test_inner(*args, **kwargs):
            if [int(x) for x in version.split(".")] <= [int(x) for x in __version__.split(".")]:
                msg = (
                    f"The function {func.__name__} must be fully removed as it is depricated"
                    f" and must be removed by version {version}"
                )
                raise AssertionError(msg)
            return func(*args, **kwargs)

        return test_inner

    return decorator_wrapper


def deprecated(message: str = "") -> typing.Callable:
    """A simplistic decorator to mark functions as deprecated. The function
    will pass a message to the user on the first use of the function

    Args:
        message (str): The message to display if the function is deprecated
    """

    def decorator_wrapper(func):
        @functools.wraps(func)
        def function_wrapper(*args, **kwargs):
            func_name = func.__name__
            if func_name not in function_wrapper.deprecated_items:
                msg = f"Function {func.__name__} is now deprecated! {message}"
                warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
                function_wrapper.deprecated_items.add(func_name)

            return func(*args, **kwargs)

        # set this up the first time the decorator is called
        function_wrapper.deprecated_items = set()

        return function_wrapper

    return decorator_wrapper


def ensure_unicode(value: KeyT, encoding: str = "utf-8") -> str:
    """Simplify checking if passed in data are bytes or a string and decode
    bytes into unicode.

    Args:
        value (str): The input string (possibly bytes)
        encoding (str): The encoding to use if input is bytes
    Returns:
        str: The encoded string
    """
    if isinstance(value, bytes):
        return value.decode(encoding)
    elif isinstance(value, list):
        raise TypeError(f"the provided value {value} is a list")
    return value


@contextlib.contextmanager
def __gzip_read(filename: PathOrStr, mode: str = "rb", encoding: str = "UTF-8") -> typing.Generator[KeyT, None, None]:
    """Context manager to correctly handle the decoding of the output of the gzip file

    Args:
        filename (str): The filename to open
        mode (str): The mode to read the data
        encoding (str): The file encoding to use
    Yields:
        str: The string data from the gzip file read
    """
    with gzip.open(filename, mode=mode, encoding=encoding) as fobj:
        yield fobj.read()


@contextlib.contextmanager
def load_file(filename: PathOrStr, encoding: str) -> typing.Generator[KeyT, None, None]:
    """Context manager to handle opening a gzip or text file correctly and
    reading all the data

    Args:
        filename (str): The filename to open
        encoding (str): The file encoding to use
    Yields:
        str: The string data from the file read
    """
    if isinstance(filename, Path):
        filename = str(filename)

    if filename[-3:].lower() == ".gz":
        with __gzip_read(filename, mode="rt", encoding=encoding) as data:
            yield data
    else:
        with open(filename, encoding=encoding) as fobj:
            yield fobj.read()


def write_file(filepath: PathOrStr, encoding: str, gzipped: bool, data: str) -> None:
    """Write the data to file either as a gzip file or text based on the
    gzipped parameter

    Args:
        filepath (str): The filename to open
        encoding (str): The file encoding to use
        gzipped (bool): Whether the file should be gzipped or not
        data (str): The data to be written out
    """
    if gzipped:
        with gzip.open(filepath, "wt") as fobj:
            fobj.write(data)
    else:
        with open(filepath, "w", encoding=encoding) as fobj:
            fobj.write(data)


def _parse_into_words(text: str) -> typing.Iterable[str]:
    """Parse the text into words; currently removes punctuation except for
    apostrophizes.

    Args:
        text (str): The text to split into words
    """
    # see: https://stackoverflow.com/a/12705513
    return re.findall(r"(\w[\w']*\w|\w)", text)
