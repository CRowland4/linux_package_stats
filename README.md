This document outlines my thoughts in building this program, and the process I went through for each step. I've created
a new repo with no git history in order to respect the desire of the source of this assignment to not be identified with
it. The source could otherwise have been gleaned from the original repo.

### Step 1 - Initial Research
- First, I'm doing some research to further familiarize myself with .deb package repos. This is surface level
"research", just for mental clarity's sake, involving asking some general questions to ChatGPT and browsing
the debian package website. Although the vast majority of work with packages is done with a shell, I find it helpful to
lay eyes on exactly what I'm working with.
- I see the basic structure of the package storage.
    - There are three top layer package lists - those in the **stable**, **testing**, and **unstable** distributions.
    - Packages are then divided into categories - Mathematics, Old Libraries, Miscellaneous, etc.
    - Each package page has the list of architectures for which that package is available, and with each architecture is
a link to browse the list of files that come with that package/architecture combo.
- I now have a much better mental image of package storage, and can move on.

### Step 2 - Review the provided link describing a repository's "Contents index"
- The description seems simple enough, but I always like to have a visual reference, so I'm going to grab an example of
one of these files to keep in my project repo for reference as I work.
  - I grabbed one from the provided Debian mirror, and copied a few lines into the file contents_index_example for easy
reference.
- I make a note in main.py to eventually account for the fact that the file may or may not begin with a header row.

### Step 3 - Create git repo
- Now that I have something in a Python file, I create my repo and make the initial commit.
- I use the standard Python .gitignore file from the gitignore repo.

### Step 4 - Project
- From this point on, specific details outlining my though process will be in the form of comments starting with "P:" in
my .py files (for "process"). Any of these comments are there solely to document my thought process for the sake of
this technical exercise, and wouldn't be included in my normal work. More general decisions will stay in this README.
- ***User input***
  - Using the argparse module here to me seems like overkill, since I'm just expecting one thing from the user. Users
will be able to call the program first, then be presented with a welcome message with simple use instructions. But
for users that already know how the program works, the two steps of 1) calling the program and then 2) entering an
argument at the prompt can become tedious. So users will also be able to include the architecture when running the
program, so the extra step can be skipped.
  - EDIT: Changed my mind about this while writing the program, it's now run-once-and-done.
- ***Control Loop*** 
  - I'm first going to build a separate function for the control loop, while the main function handles the initially
passed architecture argument. I'll most likely refactor that on a second pass.
  - EDIT: In the end I decided to not include a control loop.
- ***udeb packages***
  - I'm not including the micro packages since they're subsets of the full packages, but including the udeb contents as 
an option is something that, in a production setting, could potentially be added in the future. So I need to make
sure that the code is flexible enough so that could be added with minimal or no refactoring of the existing code.
    - EDIT: I did end up including the udeb packages because no extra code was needed to make that work
- ***First significant issue***
  - I've come across my first significant (and unexpected) issue. I'm able to connect to the FTP server just fine,
then successfully change the directory to where the contents files are located, but I can't list the files in
the directory or download the contents of a file. After more than an hour of trying to figure out what the issue
was, I narrowed it down the UK debian FTP server.
  - This code works (US server):
  ```python
  ftp = FTP('ftp.us.debian.org')
  ftp.login()
  ftp.retrlines('LIST')
  ```
  - This throws an error (UK server):
  ```python
  ftp = FTP('ftp.uk.debian.org')
  ftp.login()
  ftp.retrlines('LIST')
  ```
  - Same thing with this code trying to retrieve a file - UK site fails, but US site works:
  ```python
  ftp = FTP('ftp.uk.debian.org')
  ftp.login()
  ftp.cwd("debian/dists/stable/main/")
  with open("TEST", 'wb') as file:
    ftp.retrbinary(f"RETR Contents-all.gz", file.write)
  ```
  - Neither active nor passive mode for the FTP connection made any difference. Setting a large timeout on the FTP
connection of a full minute also didn't help.
  - I decided to try a Bash script to do the file retrieval instead. I used WSL to
figure out which commands to use, and hit the exact same issue. I can connect and log in to the UK server, but can't
'get' any files, or view the contents of any directories. No issues with US server. Passive vs. active mode also didn't
make any difference when connecting via WSL.
  - Did some more debugging back with Python's FTP library. The error is being thrown during the creation of a socket
within the socket library, which explains why different timeouts set on the FTP connection didn't have any effect on
the time it took for the error to be thrown.
  - UK and US server behavior is identical without a VPN connection, with a VPN connection to a server in the UK,
and with a VPN connection to a server in the US.
  - My next thought is that it's something with the way I'm connecting. I have no problem accessing and downloading
files from the UK server via a web browser.
  - I was able to successfully download a file from the UK server with Python's requests library. I'm curious as to why
I'm able to use something other than an FTP connection to download a file from an FTP server. Maybe the requests library
is using an FTP connection under the hood, but in a way different from the actual FTP library. This is a networking
question I would write down to ask someone later.
- ***WSL vs. GitBash venv***
  - Another question I would write down later to ask: I'm unable to activate this project's venv via WSL. Had to use
GitBash. WSL gives the error `pyenv-virtualenv: version '3.12.1' is not a virtualenv`, which is odd because the venv I
was trying to activate uses Python 3.11, not 3.12.
    - EDIT: This problem seems to have resolved itself with no intervention on my part. Issue was most likely caused by
something PyCharm was doing, rather than some difference in the way virtual environments are handled between WSL and
PowerShell or GitBash.
- ***Caching***
  - The biggest time bottleneck here is obviously going to be the downloading and parsing of data from the FTP server. I
can use a cache to speed this up. The cache will only store the information that will be displayed to the user - top
packages with the most files associated with them - so the cache will be small. Oddly enough, the `MDTM` FTP command
works with the UK server, so I can retrieve the last modified times for each file and update the cache if necessary, so
it remains current.
- ***Manual Testing***
  - Ran some manual tests after completing the caching functionality. Works as intended. The caching reduces the runtime
down to just under 2 seconds for any of the architecture choices. That delay comes from the necessary FTP call to make
sure that the cache is current. Before caching, most architectures were taking between 6 and 8 seconds, with `all` at 16
seconds and `source` at nearly 35.
- ***Output Formatting***
  - Now I'll work on the output seen by the user.
- ***Finished First Draft***
  - First working version of the program is complete, ~12 hours total.
- ***Polish***
  - First polish step will be to add coloring to the user output, and finalize output formatting.
  - Next I'll do a light refactor run through the code, adding comments where a "why" explanation is warranted and where
I could further explain my thought process, and tidying up lines that could be cleaner.
- ***Speed***
  - Here are the current speeds for downloading each architecture, in seconds, before caching:
  ```
  all: 20.28
  amd64: 10.78
  arm64: 10.53
  armel: 7.48
  armhf: 9.66
  i386: 8.46
  mips64el: 11.47
  mipsel: 8.10
  ppc64el: 10.84
  s390x: 10.15
  source: 44.66
  ```
    - EDIT: Across different days, these speeds changed relatively dramatically regardless of code changes. It became
clear that networking speed was more responsible than I had even initially thought. I'm still happy with the efficiency
upgrades, but ultimate the network will determine how quickly the program runs, which is normal for a program relying on
any sort of network connection.
  - My next task is to try to speed this up. The first thing I did was replace my temporary storage file where I was
  writing and then reading the downloaded file to/from with a buffer. This was suggested by ChatGPT when I asked it for
  an alternative to using a temporary file, though in hindsight using a buffer should have been obvious anyway.
  - Swapping my temporary file solution for a buffer did essentially nothing to speed up the process. The
  time-consuming piece of code was actually reading the file into memory all at once with the `.readlines()` method, and
  it didn't matter if I was reading from a file or a buffer. So my next step is to use a `GzipFile` object to iterate
  over the file contents, instead of iterating over the pre-read chunk of data.
  - Next efficiency step is to stop decoding every line of bytes from the file, and only decode the ones that are going
  to go into the cache.
  - Finally, I moved the check for the header row, so it doesn't check every row in the file, only the ones cached.
  - These changes didn't seem to have much of a tangible effect on the speed, but the code is more streamlined now.
  - My computer has also been running code much slower than it should be recently, which makes legitimate speed testing
hard to do. Regardless, I'm confident that the majority of the run time now is primarily dependent on the connection to
the FTP server and the size of the files being analyzed, not code inefficiencies. 
- ***Micros***
  - Decided to add in the micros by adding the udeb- versions of the architectures to the constants file. An easy add,
no reason to exclude them, subsets of the larger indices or not.
- ***Error Handling and Logging***
  - Exception handling and logging are next. This will also involve more output formatting, in deciding what to log and
show the user, and what to log but not show in the output.
- ***Loading animation***
  - Since the requests to the debian mirror can take a few seconds, especially downloading the contents index, I added
a small dots animation so the user knows the program hasn't frozen.
- ***Tests***
  - The code is done, now to write tests.
  - Ran into a lot of issues trying to figure out how to get pytest to see the rest of my modules in source. These
import issues would be something else to write down and talk to another dev about.
- ***Final Notes***
  - Made a couple passes through the code for readability and cleanliness. Ended up finding and fixing an issue where
the animations wouldn't properly show under certain conditions. There's always something extra to find on a general
review when you're not focused on one specific piece of code, which is why I like to do them.
  - I noticed on these final passes that the git repo shows two contributors - this is due to WSL virtual environment
issues I mentioned earlier in the process. One user is from WSL and the other is from Windows.
  - I ran the program the way a user would several times for a last set of manual checks, and ran the tests to confirm
everything works correctly after the final commit.
  - I decided to keep the contents index sample I used for reference, as it could still be used as a reference later.
