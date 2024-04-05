import pytest
import requests
from source import debian_mirror


def test_read_contents_index_file(capsys):
    """Tests that the function properly alerts the user of the download status, and raises the correct exception if the
    download fails"""
    valid_architecture = "udeb-all"
    invalid_architecture = "foobar"

    # Valid architecture - user is alerted that a download is in progress, and then successful
    debian_mirror.read_contents_index_file(valid_architecture)
    valid_captured = capsys.readouterr()
    assert "Downloading" in valid_captured.out
    assert "Success" in valid_captured.out

    # Exception is raised when an invalid architecture is requested
    with pytest.raises(requests.exceptions.RequestException):
        debian_mirror.read_contents_index_file(invalid_architecture)

    # Invalid architecture - user is alerted that a download is in progress, and that the download fails
    invalid_captured = capsys.readouterr()
    assert "Downloading" in invalid_captured.out
    assert "Failed" in invalid_captured.out

    return


def test_get_last_modified_timestamp():
    """Tests that an empty string is returned when a valid timestamp can't be retrieved."""
    # P: To actually test if the correct timestamp was returned from the server, the function itself would have to be
    #    copied here line-by-line and then compared to the version in debian_mirror.py, which wouldn't make sense to
    #    have in a test. So I just test the result of passing an invalid architecture
    invalid_architecture = "foo"
    result = debian_mirror.get_last_modified_timestamp(invalid_architecture)
    assert result == ""

    return
