import unittest
from deadshot.services.github.git_diff_parser import *

with open("tests/fixtures/test.diff") as test_diff_file:
    test_diff = test_diff_file.read()

expected_diff_added = [
  "",
  "// NOTE: For SignatureV4 to work, this must not be removed. SignatureV4 requires",
  "// this parameter.",
  "'credentials.cache' => $cacheAdapter,",
  "",
  "// So far the only use of this arg is to use v4. Due to other signing methods",
  "// and SignatureInterfaces (such as v3http), we'll default to forcing v4 if",
  "// no value is given to prevent S3Client defaulting to v2 which will fail to",
  "// work on 6/24/2019.",
  "if (empty($signatureVersion)) {",
  "$factoryOptions[\"signature\"] = self::$S3_SIGNATURE_v4;"
]

expected_diff_removed = [
  "'credentials.cache' => $cacheAdapter",
  "",
  "if ($signatureVersion) {",
  "$factoryOptions[\"signature\"] = $signatureVersion;"
]


class TestDiffParser(unittest.TestCase):

    def test_diff_parses(self):
        diff_parser = GithubDiffProcessor("abc", "token", test_diff)
        lines = []
        for diff_file in diff_parser.diff_files():
            # print(diff_file)
            for diff_line in diff_file.diff_lines():
                lines.append(diff_line)
                # print(diff_line)

        added_lines = [line.value for line in lines if line.line_type == DiffLine.LINE_TYPE_ADDED]
        assert added_lines == expected_diff_added, f"[!] added lines do not match: {added_lines}"

        removed_lines = [line.value for line in lines if line.line_type == DiffLine.LINE_TYPE_REMOVED]
        assert removed_lines == expected_diff_removed, f"[!] removed lines do not match: {removed_lines}"