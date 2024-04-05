"""Functions here are meant to be used as the action for the Animation class."""
from colorama import Fore


def dots() -> None:
    print(f"{Fore.GREEN}.{Fore.RESET}", end="", flush=True)
    return
