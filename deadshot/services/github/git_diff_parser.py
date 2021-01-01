import requests
import unidiff
import os
import logging
logger = logging.getLogger()

# This file defines classes and methods to get diff file types and lines of a Pull Request
# for which the task was initiated


class DiffFileTypes:
    # This class is used to get the file type in the Pull Request currently being scanned
    PYTHON = "py"
    PYTHON_REQUIREMENTS = "python_requirements"
    JAVA = "java"
    MAVEN = "maven"
    PHP = "php"
    SCALA = "scala"
    JAVASCRIPT = "js"
    RUBY = "ruby"
    C = "c"
    CPP = "cpp"

    @classmethod
    def get_filetype_from_filename(cls, fullpath):
        # if it's part of a filepath = /ab/c/ds/dd.java
        filename = fullpath.split("/")[-1]
        endings = [
            (".java", cls.JAVA),
            (".py", cls.PYTHON),
            (".php", cls.PHP),
            (".scala", cls.SCALA),
            (".rb", cls.RUBY),
            (".js", cls.JAVASCRIPT),
            (".c", cls.C),
            (".cpp", cls.CPP),
            ("requirements.txt", cls.PYTHON_REQUIREMENTS)
        ]
        for ending in endings:
            if filename.endswith(ending[0]):
                return ending[1]
        return None


class DiffFile:
    def __init__(self, patch_file):
        self.patch_file = patch_file
        self.full_filename = patch_file.path
        self.source_file = patch_file.source_file
        self.target_file = patch_file.target_file
        self.file_type = DiffFileTypes.get_filetype_from_filename(
            self.full_filename
        )

    def __str__(self):
        return "{} ({})".format(
            self.full_filename,
            self.file_type
        )

    def diff_lines(self):
        for patch in self.patch_file:
            for line in patch:
                diff_line = DiffLine(
                    diff_file=self,
                    value=line.value,
                    line_type=line.line_type,
                    source_line_number=line.source_line_no,
                    target_line_number=line.target_line_no
                )
                yield diff_line


class DiffLine:
    LINE_TYPE_ADDED = '+'
    LINE_TYPE_REMOVED = '-'
    LINE_TYPE_CONTEXT = ' '
    LINE_TYPE_EMPTY = ''
    LINE_TYPE_NO_NEWLINE = '\\'
    LINE_VALUE_NO_NEWLINE = ' No newline at end of file'

    def __init__(
            self,
            diff_file,
            value,
            line_type,
            source_line_number,
            target_line_number):
        self.line_type = line_type
        self.line_number = target_line_number
        self.source_line_number = source_line_number
        self.diff_file = diff_file
        self.value = value.strip()

    def __str__(self):
        return "<DiffLine {} {} {}>".format(
            self.line_type,
            self.line_number,
            self.value
        )


class GithubDiffProcessorException(Exception):
    pass


class GithubDiffProcessor:
    def __init__(self, diff_url, token, diff_str=None):
        self.token = token
        self.diff_url = diff_url
        # Lazy load diff_str
        self.diff_str = diff_str

    def load_diff_from_url(self):
        headers = {
            "Authorization": f"token {self.token}",
            # "Accept" header controls what API returns to us
            # this will return the diff
            "Accept": "application/vnd.github.v3.diff"
        }
        response = requests.get(self.diff_url, headers=headers)
        self.diff_str = response.text
        return self.diff_str

    def diff_files(self):
        if self.diff_str is None:
            self.diff_str = self.load_diff_from_url()

        patch_files = unidiff.PatchSet(self.diff_str)
        for patch_file in patch_files:
            yield DiffFile(patch_file)
