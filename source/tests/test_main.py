import gzip
import os.path
from source import constants as cons
from source import main


# P: The main(), analyze_architecture_contents(), get_top_package_file_counts(), and get_cache() functions consist
#    almost entirely of other function calls, so they don't have their own unit tests. main.sort_package_file_counts()
#    is implicitly tested within test_count_package_file_associations, so it also doesn't have its own unit test.

def test_is_user_input_valid(capsys):
    # No architecture passed. Function should return False and let the user know how to format the input
    test_no_argument = main.is_user_input_valid(["./main.py"])
    captured_no_argument = capsys.readouterr()
    assert test_no_argument is False
    assert "Usage:" in captured_no_argument.out

    # Invalid architecture is passed. Function should return False, let the user know, and list the valid choices
    test_invalid_arch1 = main.is_user_input_valid(["./main.py", "foo"])
    test_invalid_arch2 = main.is_user_input_valid(["./main.py", "udeb-source"])
    captured_invalid_arch = capsys.readouterr()
    assert test_invalid_arch1 is False
    assert test_invalid_arch2 is False
    assert "Invalid architecture" in captured_invalid_arch.out
    for architecture in cons.VALID_ARCHITECTURES:
        assert architecture in captured_invalid_arch.out

    # Valid architecture is passed
    for architecture in cons.VALID_ARCHITECTURES:
        test_valid_input = main.is_user_input_valid(["./main.py", architecture])
        assert test_valid_input is True

    # Too many arguments are passed. Function should let the user know how to format the input
    test_too_many_args1 = main.is_user_input_valid(["./main.py", "foo", "bar", "baz"])  # Too many args, all invalid
    test_too_many_args2 = main.is_user_input_valid(["./main.py", "arm64", "all", "armel"])  # All valid architectures
    test_too_many_args3 = main.is_user_input_valid(["./main.py", "source", "foo", "armhf"])  # Mix of valid and invalid
    captured_too_many_args = capsys.readouterr()
    assert test_too_many_args1 is False
    assert test_too_many_args2 is False
    assert test_too_many_args3 is False
    assert "Usage:" in captured_too_many_args.out

    return


def test_exists_valid_cache_entry():
    valid_timestamp = "up-to-date"
    invalid_timestamp = "Not up-to-date"

    no_entry = {}
    bad_timestamp_not_enough_packages = {"last_modified": invalid_timestamp,
                                         "packages": {f"package{i}": 1 for i in range(cons.SHOW_COUNT - 3)}}
    bad_timestamp_excess_packages = {"last_modified": invalid_timestamp,
                                     "packages": {f"package{i}": 1 for i in range(cons.SHOW_COUNT + 3)}}
    bad_timestamp_just_enough_packages = {"last_modified": invalid_timestamp,
                                          "packages": {f"package{i}": 1 for i in range(cons.SHOW_COUNT)}}
    good_timestamp_not_enough_packages = {"last_modified": valid_timestamp,
                                          "packages": {f"package{i}": 1 for i in range(cons.SHOW_COUNT - 3)}}
    good_timestamp_excess_packages = {"last_modified": valid_timestamp,
                                      "packages": {f"package{i}": 1 for i in range(cons.SHOW_COUNT + 3)}}
    good_timestamp_just_enough_packages = {"last_modified": valid_timestamp,
                                           "packages": {f"package{i}": 1 for i in range(cons.SHOW_COUNT)}}

    assert main.exists_valid_cache_entry(no_entry, valid_timestamp) is False
    assert main.exists_valid_cache_entry(bad_timestamp_not_enough_packages, valid_timestamp) is False
    assert main.exists_valid_cache_entry(bad_timestamp_excess_packages, valid_timestamp) is False
    assert main.exists_valid_cache_entry(bad_timestamp_just_enough_packages, valid_timestamp) is False
    assert main.exists_valid_cache_entry(good_timestamp_not_enough_packages, valid_timestamp) is False
    assert main.exists_valid_cache_entry(good_timestamp_excess_packages, valid_timestamp) is True
    assert main.exists_valid_cache_entry(good_timestamp_just_enough_packages, valid_timestamp) is True

    return


def test_count_package_file_associations():
    """The zipped test_contents_index.gz file consists of free text at the top, a header row of "FILE LOCATION" to start
    the table, several invalid rows, and exactly 100 valid packages, all according to the wiki specifications for the
    format of a contents index.

    The 100 packages are associated with the amount of files that will place them in the sorted list in accordance with
    the number in the name of the package. For example, valid_package1 will have the fewest amount of associated files,
    valid_package_2 the second most, and so on.

    Packages 51-100 are listed in comma separated pairs to test the function's ability to count a file for multiple
    packages, so 51 and 52 will have the same amount of files (51), as will 53 and 54 (53), and so on. So from 51 on,
    each odd numbered package should have a matching number of file associations, and the files associated with each
    even numbered package should be the same as the odd number before it.

    This implicitly tests main.sort_package_file_counts() as well, since count_package_file_associations() calls that
    function on the result before returning.
    """
    test_contents_index = os.path.join("tests", "test_contents_index.gz")
    with gzip.GzipFile(filename=test_contents_index, mode="rb") as file:
        file_counts = main.count_package_file_associations(file)

    # The correct amount of entries is returned
    assert len(file_counts) == cons.CACHE_SIZE  # main.count_package_file_associations() returns CACHE_SIZE entries

    # Files are counted correctly, and only for valid packages
    for package, count in file_counts.items():
        package_number = package.removeprefix("valid_package")  # Each valid package is named 'valid_package<num>'
        assert package_number.isnumeric()  # No packages named anything else should appear in the count

        if not package_number.isnumeric():
            continue  # To avoid throwing an exception if the previous assertion fails

        package_number = int(package_number)
        if package_number <= 50 or (package_number > 50 and package_number % 2 == 1):
            assert count == package_number
        else:
            assert count == package_number - 1

    # Counts are sorted correctly
    file_count_tuples = [(name, number) for name, number in file_counts.items()]
    assert file_count_tuples == sorted(file_count_tuples, key=lambda x: x[1], reverse=True)

    return


def test_print_architecture_statistics(capsys):
    test_contents_index = os.path.join("tests", "test_contents_index.gz")
    with gzip.GzipFile(filename=test_contents_index, mode="rb") as file:
        file_counts = main.count_package_file_associations(file)

    main.print_architecture_statistics(file_counts)
    captured = capsys.readouterr()

    # Table header appears
    assert "PACKAGE" in captured.out
    assert "ASSOCIATED FILES" in captured.out

    # Exactly cons.SHOW_COUNT results appear
    assert str(cons.SHOW_COUNT + 1) not in captured.out
    for i in range(1, cons.SHOW_COUNT + 1):
        assert f"{i}." in captured.out

    # Each package name is printed to the screen along with its file association count
    for package, count in list(file_counts.items())[:cons.SHOW_COUNT]:
        assert package in captured.out
        assert str(count) in captured.out

    return
