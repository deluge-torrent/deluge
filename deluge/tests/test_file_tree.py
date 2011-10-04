from twisted.trial import unittest
from deluge.ui.common import ExtFileTree

class ExtFileTreeTestCase(unittest.TestCase):

    def test_simple_tree(self):
        paths = [
            "SomeRootFolder/file1",
            "SomeRootFolder/file2",
            "SomeRootFolder/subfolder1/subfile1",
            "SomeRootFolder/subfolder1/subfile2"
        ]
        tree = ExtFileTree(paths)
        self.assertEqual(tree.tree, {"children": [
            {"text": "SomeRootFolder", "children": [
                {"text": "file1"},
                {"text": "file2"},
                {"text": "subfolder1", "children": [
                    {"text": "subfile1"},
                    {"text": "subfile2"}
                ]}
            ]}
        ], "text": ""})

    def test_tree_walk(self):
        paths = [
            "SomeRootFolder/file1",
            "SomeRootFolder/file2",
            "SomeRootFolder/subfolder1/subfile1",
            "SomeRootFolder/subfolder1/subfile2"
        ]
        tree = ExtFileTree(paths)
        for path, obj in tree.walk():
            if path == "SomeRootFolder/file1":
                obj["size"] = 1024

        self.assertEqual(tree.tree, {"children": [
            {"text": "SomeRootFolder", "children": [
                {"text": "file1", "size": 1024},
                {"text": "file2"},
                {"text": "subfolder1", "children": [
                    {"text": "subfile1"},
                    {"text": "subfile2"}
                ]}
            ]}
        ], "text": ""})
