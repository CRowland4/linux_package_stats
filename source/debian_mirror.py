"""Functions to be used for direct communication with or information retrieval from ftp.uk.debian.org"""

#  P: This is its own module for the sake of boundaries. These functions communicate directly with the external server,
#     so they're kept separate from the rest of the project.
from animations.animation import Animation
import constants as cons
import ftplib
import logging
import requests


def read_contents_index_file(arch: str) -> bytes:
    """Returns the bytes of the gzipped contents index file for <arch>"""
    architecture_contents_index_url = f"http://{cons.HOST}/{cons.CONTENT_INDICES_SLUG}/Contents-{arch}.gz"
    print(f"{cons.GREEN}Downloading {cons.RESET}{arch}{cons.GREEN} contents index{cons.RESET}", end="")

    animation = Animation(cons.DEFAULT_ANIMATION)
    animation.start()
    response = requests.get(architecture_contents_index_url)
    animation.stop()

    if response.status_code != 200:
        print(f"{cons.RED} Failed{cons.RESET}")
        message = f"Download failure: {architecture_contents_index_url}; {response.status_code} - {response.reason}"
        logging.critical(message)
        raise requests.exceptions.RequestException()

    print(f"{cons.GREEN} Success{cons.RESET}")
    return response.content


def get_last_modified_timestamp(arch: str) -> str:
    """Returns the timestamp of the last modification time for the Contents index file of the given architecture"""
    # P: This function failing only means that, if a cache exists for this architecture choice already, it can't
    #    be validated as current, so the file will have to be downloaded again. So I just log and move on, no need to
    #    stop the program.
    timestamp = ""
    try:
        ftp = ftplib.FTP(cons.HOST)
        ftp.login()
        ftp.cwd(cons.CONTENT_INDICES_SLUG)
        timestamp = ftp.sendcmd(f"MDTM Contents-{arch}.gz")
        ftp.quit()
    except ftplib.Error as e:
        logging.info(f"Failed reading last modify time of contents index for {cons.RESET}{arch}; ftplib error: {e}")
    finally:
        return timestamp
