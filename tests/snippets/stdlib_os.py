import os
import time
import stat

from testutils import assert_raises

fd = os.open('README.md', os.O_RDONLY)
assert fd > 0

os.close(fd)
assert_raises(OSError, lambda: os.read(fd, 10))
assert_raises(FileNotFoundError, lambda: os.open('DOES_NOT_EXIST', os.O_RDONLY))
assert_raises(FileNotFoundError, lambda: os.open('DOES_NOT_EXIST', os.O_WRONLY))
assert_raises(FileNotFoundError, lambda: os.rename('DOES_NOT_EXIST', 'DOES_NOT_EXIST 2'))

try:
	os.open('DOES_NOT_EXIST', 0)
except OSError as err:
	assert err.errno == 2



assert os.O_RDONLY == 0
assert os.O_WRONLY == 1
assert os.O_RDWR == 2

ENV_KEY = "TEST_ENV_VAR"
ENV_VALUE = "value"

assert os.getenv(ENV_KEY) == None
assert ENV_KEY not in os.environ
assert os.getenv(ENV_KEY, 5) == 5
os.environ[ENV_KEY] = ENV_VALUE
assert ENV_KEY in os.environ
assert os.getenv(ENV_KEY) == ENV_VALUE
del os.environ[ENV_KEY]
assert ENV_KEY not in os.environ
assert os.getenv(ENV_KEY) == None

if os.name == "posix":
	os.putenv(ENV_KEY, ENV_VALUE)
	os.unsetenv(ENV_KEY)
	assert os.getenv(ENV_KEY) == None

assert os.curdir == "."
assert os.pardir == ".."
assert os.extsep == "."

if os.name == "nt":
	assert os.sep == "\\"
	assert os.linesep == "\r\n"
	assert os.altsep == "/"
	assert os.pathsep == ";"
else:
	assert os.sep == "/"
	assert os.linesep == "\n"
	assert os.altsep == None
	assert os.pathsep == ":"

assert os.fspath("Testing") == "Testing"
assert os.fspath(b"Testing") == b"Testing"
assert_raises(TypeError, lambda: os.fspath([1,2,3]))

class TestWithTempDir():
	def __enter__(self):
		if os.name == "nt":
			base_folder = os.environ["TEMP"]
		else:
			base_folder = "/tmp"
		name = os.path.join(base_folder, "rustpython_test_os_" + str(int(time.time())))
		os.mkdir(name)
		self.name = name
		return name

	def __exit__(self, exc_type, exc_val, exc_tb):
		# TODO: Delete temp dir
		pass


class TestWithTempCurrentDir():
	def __enter__(self):
		self.prev_cwd = os.getcwd()

	def __exit__(self, exc_type, exc_val, exc_tb):
		os.chdir(self.prev_cwd)


FILE_NAME = "test1"
FILE_NAME2 = "test2"
FILE_NAME3 = "test3"
SYMLINK_FILE = "symlink"
SYMLINK_FOLDER = "symlink1"
FOLDER = "dir1"
CONTENT = b"testing"
CONTENT2 = b"rustpython"
CONTENT3 = b"BOYA"

with TestWithTempDir() as tmpdir:
	fname = os.path.join(tmpdir, FILE_NAME)
	fd = os.open(fname, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
	assert os.write(fd, CONTENT2) == len(CONTENT2)
	os.close(fd)

	fd = os.open(fname, os.O_WRONLY | os.O_APPEND)
	assert os.write(fd, CONTENT3) == len(CONTENT3)
	os.close(fd)

	assert_raises(FileExistsError, lambda: os.open(fname, os.O_WRONLY | os.O_CREAT | os.O_EXCL))

	fd = os.open(fname, os.O_RDONLY)
	assert os.read(fd, len(CONTENT2)) == CONTENT2
	assert os.read(fd, len(CONTENT3)) == CONTENT3
	os.close(fd)

	fname3 = os.path.join(tmpdir, FILE_NAME3)
	os.rename(fname, fname3)
	assert os.path.exists(fname) == False
	assert os.path.exists(fname3) == True

	fd = os.open(fname3, 0)
	assert os.read(fd, len(CONTENT2) + len(CONTENT3)) == CONTENT2 + CONTENT3
	os.close(fd)

	os.rename(fname3, fname)
	assert os.path.exists(fname3) == False
	assert os.path.exists(fname) == True

	# wait a little bit to ensure that the file times aren't the same
	time.sleep(0.1)

	fname2 = os.path.join(tmpdir, FILE_NAME2)
	with open(fname2, "wb"):
		pass
	folder = os.path.join(tmpdir, FOLDER)
	os.mkdir(folder)

	symlink_file = os.path.join(tmpdir, SYMLINK_FILE)
	os.symlink(fname, symlink_file)
	symlink_folder = os.path.join(tmpdir, SYMLINK_FOLDER)
	os.symlink(folder, symlink_folder)

	names = set()
	paths = set()
	dirs = set()
	dirs_no_symlink = set()
	files = set()
	files_no_symlink = set()
	symlinks = set()
	for dir_entry in os.scandir(tmpdir):
		names.add(dir_entry.name)
		paths.add(dir_entry.path)
		if dir_entry.is_dir():
			assert stat.S_ISDIR(dir_entry.stat().st_mode) == True
			dirs.add(dir_entry.name)
		if dir_entry.is_dir(follow_symlinks=False):
			assert stat.S_ISDIR(dir_entry.stat().st_mode) == True
			dirs_no_symlink.add(dir_entry.name)
		if dir_entry.is_file():
			files.add(dir_entry.name)
			assert stat.S_ISREG(dir_entry.stat().st_mode) == True
		if dir_entry.is_file(follow_symlinks=False):
			files_no_symlink.add(dir_entry.name)
			assert stat.S_ISREG(dir_entry.stat().st_mode) == True
		if dir_entry.is_symlink():
			symlinks.add(dir_entry.name)

	assert names == set([FILE_NAME, FILE_NAME2, FOLDER, SYMLINK_FILE, SYMLINK_FOLDER])
	assert paths == set([fname, fname2, folder, symlink_file, symlink_folder])
	assert dirs == set([FOLDER, SYMLINK_FOLDER])
	assert dirs_no_symlink == set([FOLDER])
	assert files == set([FILE_NAME, FILE_NAME2, SYMLINK_FILE])
	assert files_no_symlink == set([FILE_NAME, FILE_NAME2])
	assert symlinks == set([SYMLINK_FILE, SYMLINK_FOLDER])

	# Stat
	stat_res = os.stat(fname)
	print(stat_res.st_mode)
	assert stat.S_ISREG(stat_res.st_mode) == True
	print(stat_res.st_ino)
	print(stat_res.st_dev)
	print(stat_res.st_nlink)
	print(stat_res.st_uid)
	print(stat_res.st_gid)
	print(stat_res.st_size)
	assert stat_res.st_size == len(CONTENT2) + len(CONTENT3)
	print(stat_res.st_atime)
	print(stat_res.st_ctime)
	print(stat_res.st_mtime)
	# test that it all of these times are greater than the 10 May 2019, when this test was written
	assert stat_res.st_atime > 1557500000
	assert stat_res.st_ctime > 1557500000
	assert stat_res.st_mtime > 1557500000

	stat_file2 = os.stat(fname2)
	print(stat_file2.st_ctime)
	assert stat_file2.st_ctime > stat_res.st_ctime

	# wait a little bit to ensures that the access/modify time will change
	time.sleep(0.1)

	old_atime = stat_res.st_atime
	old_mtime = stat_res.st_mtime

	fd = os.open(fname, os.O_RDWR)
	os.write(fd, CONTENT)
	os.fsync(fd)

	# wait a little bit to ensures that the access/modify time is different
	time.sleep(0.1)

	os.read(fd, 1)
	os.fsync(fd)
	os.close(fd)

	# retrieve update file stats
	stat_res = os.stat(fname)
	print(stat_res.st_atime)
	print(stat_res.st_ctime)
	print(stat_res.st_mtime)
	if os.name != "nt":
		# access time on windows has a resolution ranging from 1 hour to 1 day
		# https://docs.microsoft.com/en-gb/windows/desktop/api/minwinbase/ns-minwinbase-filetime
		assert stat_res.st_atime > old_atime, "Access time should be update"
		assert stat_res.st_atime > stat_res.st_mtime
	assert stat_res.st_mtime > old_mtime, "Modified time should be update"

	# stat default is follow_symlink=True
	os.stat(fname).st_ino == os.stat(symlink_file).st_ino
	os.stat(fname).st_mode == os.stat(symlink_file).st_mode

	os.stat(fname, follow_symlinks=False).st_ino == os.stat(symlink_file, follow_symlinks=False).st_ino
	os.stat(fname, follow_symlinks=False).st_mode == os.stat(symlink_file, follow_symlinks=False).st_mode

	# os.path
	assert os.path.exists(fname) == True
	assert os.path.exists("NO_SUCH_FILE") == False
	assert os.path.isfile(fname) == True
	assert os.path.isdir(folder) == True
	assert os.path.isfile(folder) == False
	assert os.path.isdir(fname) == False

	assert os.path.basename(fname) == FILE_NAME
	assert os.path.dirname(fname) == tmpdir

	with TestWithTempCurrentDir():
		os.chdir(tmpdir)
		assert os.getcwd() == tmpdir
		os.path.exists(FILE_NAME)

# supports
assert isinstance(os.supports_fd, set)
assert isinstance(os.supports_dir_fd, set)
assert isinstance(os.supports_follow_symlinks, set)
