from animations.animation_functions import dots
from colorama import Fore


# Colors for console output
CYAN = Fore.CYAN
GREEN = Fore.GREEN
GREY = Fore.LIGHTBLACK_EX
RED = Fore.RED
RESET = Fore.RESET
YELLOW = Fore.YELLOW

# Animation constants
ANIMATION_DELAY = 0.8
DEFAULT_ANIMATION = dots

# P: The sufficiently small amount of architectures warrants the manual creation of this list to compare user
#    input against. A set is used over a list or tuple for lookup speed. Makes little difference with this many items,
#    but I like to be in the habit of considering these things.
VALID_ARCHITECTURES = {"all", "amd64", "arm64", "armel", "armhf", "i386", "mips64el", "mipsel", "ppc64el", "s390x",
                       "source", "udeb-all", "udeb-amd64", "udeb-arm64", "udeb-armel", "udeb-armhf", "udeb-i386",
                       "udeb-mips64el", "udeb-mipsel", "udeb-ppc64el", "udeb-s390x"}

# This many package/file-count items will be shown to the user
# NOTE: The show count should not exceed the cache size. An error won't be thrown, but if this happens the cache size
#       will determine how many items the user sees.
SHOW_COUNT = 10

# This many package/file-count items will be cached, so the display can increase if desired
# NOTE: Tests will work with a CACHE_SIZE up to 100
CACHE_SIZE = 30

# Run time outputs
PASSING_ARGUMENT_INSTRUCTIONS = f"\n{CYAN}Usage:{RESET} python ./main.py <architecture>\n"
ARCHITECTURES_LIST = f"\n{CYAN}Valid architectures:{RESET} {', '.join(sorted(list(VALID_ARCHITECTURES)))}\n"
OUTPUT_SEPARATOR = RED + '~' * 80 + RESET

# URLs and file paths
HOST = "ftp.uk.debian.org"
CONTENT_INDICES_SLUG = "debian/dists/stable/main"
CACHE_PATH = "architecture_cache.json"
