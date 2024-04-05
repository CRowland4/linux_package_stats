import os
import traceback

from animations.animation import Animation
from collections import defaultdict
import constants as cons
import debian_mirror as deb
import gzip
import io
import json
import logging
import requests.exceptions
import sys


def main() -> None:  # P: Conventionally, main returns nothing. Python doesn't require this, so still worth a type hint.
    # P: I decided not to include a control loop, as that would require an extra step from the user in order to exit the
    #    program. The benefit of being able to enter more architecture choices without running the program again
    #    isn't enough to outweigh the combined cost of the time to write the loop plus the need for the user to manually
    #    exit the program.

    logging.basicConfig(filename="./logs.log", level=logging.WARNING, encoding="utf-8",
                        format="%(asctime)s -- %(levelname)s -- %(message)s")

    if is_user_input_valid(sys.argv):
        analyze_architecture_contents(sys.argv[1])

    return


# P: Put user input handling into its own function for easier testing.
def is_user_input_valid(arguments: list[str]) -> bool:
    """Returns true if user input is valid, else returns false and lets the user know why their input is invalid."""
    if len(arguments) != 2:
        logging.info(f"Invalid program usage. Input received: {arguments}")
        print(cons.PASSING_ARGUMENT_INSTRUCTIONS)
        return False
    elif arguments[1] not in cons.VALID_ARCHITECTURES:
        logging.info(f"Invalid architecture passed to program: {arguments[1]}")
        print(f"\n{cons.RED}Invalid architecture:{cons.RESET} {arguments[1]}")
        print(cons.ARCHITECTURES_LIST)
        return False

    return True


def analyze_architecture_contents(arch: str) -> None:  # P: Function name makes more sense now, so no change
    """The top level function for downloading, parsing, and displaying statistics from the Contents file for
    <arch>."""
    cache = get_cache()
    arch_stats = cache.get(arch, {})

    print(f"{cons.GREEN}Checking cache for up-to-date {cons.RESET}{arch}{cons.GREEN} statistics{cons.RESET}", end="")
    animation = Animation(cons.DEFAULT_ANIMATION)
    animation.start()
    server_timestamp = deb.get_last_modified_timestamp(arch)
    valid_entry = exists_valid_cache_entry(arch_stats, server_timestamp)
    animation.stop()

    if valid_entry:
        print(f"{cons.GREEN} Found{cons.RESET}")
    else:
        print(f"{cons.YELLOW} Not found{cons.RESET}")
        content = deb.read_contents_index_file(arch)
        cache[arch] = {"last_modified": server_timestamp, "packages": get_top_package_file_counts(content)}

        with open(cons.CACHE_PATH, "w") as json_file:
            json.dump(cache, json_file)

    print_architecture_statistics(cache[arch]["packages"])
    return


def exists_valid_cache_entry(arch_stats: dict, server_timestamp: str) -> bool:
    """Checks if the architecture statistics passed are valid.

    To be considered valid, statistics must be non-emtpy, contain at least <cons.SHOW_COUNT> entries, and have a
    last_modified timestamp equal to that of the last modified timestamp from the debian mirror."""
    # P: Made this validation a separate function for easier testing
    if not arch_stats:
        return False
    elif arch_stats["last_modified"] != server_timestamp:
        return False
    elif len(arch_stats["packages"]) < cons.SHOW_COUNT:
        return False
    else:
        return True


def get_top_package_file_counts(zipped_arch_contents: bytes) -> dict[str, int]:
    """Returns a sorted dictionary where each key is a package name, and each value is an integer count of how many
    files are associated with that package in <zipped_arch_contents>.

    The returned dictionary contains the amount of items specified by <cons.CACHE_SIZE>, and is sorted in descending
    order of file association counts. Any malformed entries as defined by the debian wiki below will be discarded
    as it suggests.

    "
    Contents indices begin with zero or more lines of free form text followed by a table mapping filenames to one or
    more packages. The table SHALL have two columns, separated by one or more spaces. The first row of the table SHOULD
    have the columns "FILE" and "LOCATION", the following rows shall have the following columns:

    1. A filename relative to the root directory, without leading .
    2. A list of qualified package names, separated by comma.

    # P: I did not include the piece in the wiki about the deprecated format of listing packages, because the naming
    #    convention of the packages shouldn't affect their inclusion/exclusion from the statistics output.

    Clients should ignore lines not conforming to this scheme. Clients should correctly handle file names containing
    white space characters (possibly taking advantage of the fact that package names cannot include white space
    characters).
    "
    """
    print(f"{cons.GREEN}Analyzing file{cons.RESET}", end="")
    animation = Animation(cons.DEFAULT_ANIMATION)
    animation.start()

    with io.BytesIO(zipped_arch_contents) as compressed_bytes:
        with gzip.GzipFile(fileobj=compressed_bytes, mode="rb") as zipped_file:
            file_counts = count_package_file_associations(zipped_file)

    animation.stop()
    print(f"{cons.GREEN} Complete{cons.RESET}")
    return file_counts


def count_package_file_associations(zipped_file: gzip.GzipFile) -> dict[str, int]:
    """Helper function to get_top_package_file_counts()"""
    file_counter = defaultdict(int)
    for line in zipped_file:
        tokens = line.split()
        # Each table entry should have at least two columns, else it's malformed.
        # Since each file is relative to the root directory, the path should contain at least one "/". If the
        #   first token of a line doesn't, it's either malformed or part of the optional beginning text, and
        #   should be excluded. This also takes care of a potential "FILE LOCATION" header row.
        if (len(tokens) < 2) or (b"/" not in b"".join(tokens[0:-1])):
            continue

        for package in tokens[-1].split(b","):  # Wiki says that packages are comma-separated with no spaces
            file_counter[package] += 1

    return sort_package_file_counts(file_counter)


def sort_package_file_counts(counts: dict[bytes, int]) -> dict[str, int]:
    """Sorts <counts> in descending order according to its integer values and returns the top <cons.CACHE_SIZE>."""
    tuples = [(package, file_count) for package, file_count in counts.items()]
    tuples.sort(key=lambda package_count: package_count[1], reverse=True)
    sorted_pairs = {package.decode(): file_count for package, file_count in tuples[:cons.CACHE_SIZE]}
    return sorted_pairs


def print_architecture_statistics(package_file_counts: dict[str, int]) -> None:
    """Prints formatted statistics to stdout."""
    # P: Whenever I use integers in my code, I always try to avoid "magic numbers". If there is a reason to use an
    #    integer and the reason for choosing it isn't obvious (the counter for i and the mod 2 for color alternation
    #    are obvious in the way they are used in this context), I either store the number in a constant if I think it
    #    has a chance of being used elsewhere, or write an explanatory comment explaining its use, as in the case of the
    #    4 and 5 here. These are numbers to handle spacing in very particular, one-off contexts. Without the comment,
    #    another dev may waste time trying to figure out why they were chosen, or hesitate to change them for fear of
    #    side effects.
    len_longest = max([len(name) for name in list(package_file_counts.keys())[:cons.SHOW_COUNT]])
    # The '4' for the spaces below is just a style choice to align "ASSOCIATED FILES" with the numbers in the column
    header = f"\n\t{cons.RED}      PACKAGE{' ' * (len_longest - len('Package') - 4)}ASSOCIATED FILES{cons.RESET}"
    print(header)

    i = 1
    alternating_colors = (cons.GREY, cons.RESET)
    for package, file_count in list(package_file_counts.items())[:cons.SHOW_COUNT]:
        color = alternating_colors[i % 2]
        number_of_spaces = len_longest - len(package) - len(str(i)) + 5  # 5 is also just a style choice
        statistic_row = f"\n\t{cons.RED}{i}. {color}{package}{' ' * number_of_spaces}{file_count}"
        print(statistic_row)
        i += 1

    print(cons.RESET)
    return


def get_cache() -> dict:
    """Retrieves and returns the cache of architecture-specific packages and their file counts."""
    if os.stat(cons.CACHE_PATH).st_size == 0:
        return {}

    with open(cons.CACHE_PATH, "r") as file:
        cache = json.load(file)

    return cache


if __name__ == '__main__':
    try:
        print(f"\n{cons.OUTPUT_SEPARATOR}")
        main()
    except requests.exceptions.RequestException:  # Manually-raised program-ending errors go here
        print("\nExiting program")
    except Exception as error:
        formatted_error = traceback.format_exception(error)
        error_location = formatted_error[-2]
        error_message = formatted_error[-1]
        print(f"{cons.RED}Unexpected error occurred. Check logs for details.{cons.RESET}")
        logging.critical(f"Unexpected error. Location: {error_location} -- Message: {error_message}")
    finally:
        print(f"{cons.OUTPUT_SEPARATOR}\n")

    # P: I always have top-level error handling to catch things I haven't explicitly accounted for in the body of the
    #    program.
