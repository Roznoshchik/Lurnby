# Copyright (c) 2013 AndroWiiid <androwiiid@gmail.com>
# Copyright (c) 2014-2016, 2018-2019 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Google, Inc.
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2018 Anthony Sottile <asottile@umich.edu>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2019 Ashley Whetter <ashley@awhetter.co.uk>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

import platform
import unittest

import _io
from astroid.builder import AstroidBuilder
from astroid.raw_building import (
    attach_dummy_node,
    build_module,
    build_class,
    build_function,
    build_from_import,
)
from astroid import test_utils


class RawBuildingTC(unittest.TestCase):
    def test_attach_dummy_node(self):
        node = build_module("MyModule")
        attach_dummy_node(node, "DummyNode")
        self.assertEqual(1, len(list(node.get_children())))

    def test_build_module(self):
        node = build_module("MyModule")
        self.assertEqual(node.name, "MyModule")
        self.assertEqual(node.pure_python, False)
        self.assertEqual(node.package, False)
        self.assertEqual(node.parent, None)

    def test_build_class(self):
        node = build_class("MyClass")
        self.assertEqual(node.name, "MyClass")
        self.assertEqual(node.doc, None)

    def test_build_function(self):
        node = build_function("MyFunction")
        self.assertEqual(node.name, "MyFunction")
        self.assertEqual(node.doc, None)

    def test_build_function_args(self):
        args = ["myArgs1", "myArgs2"]
        node = build_function("MyFunction", args)
        self.assertEqual("myArgs1", node.args.args[0].name)
        self.assertEqual("myArgs2", node.args.args[1].name)
        self.assertEqual(2, len(node.args.args))

    def test_build_function_defaults(self):
        defaults = ["defaults1", "defaults2"]
        node = build_function(name="MyFunction", args=None, defaults=defaults)
        self.assertEqual(2, len(node.args.defaults))

    def test_build_function_posonlyargs(self):
        node = build_function(name="MyFunction", posonlyargs=["a", "b"])
        self.assertEqual(2, len(node.args.posonlyargs))

    def test_build_from_import(self):
        names = ["exceptions, inference, inspector"]
        node = build_from_import("astroid", names)
        self.assertEqual(len(names), len(node.names))

    @unittest.skipIf(platform.python_implementation() == "PyPy", "Only affects CPython")
    @test_utils.require_version(minver="3.0")
    def test_io_is__io(self):
        # _io module calls itself io. This leads
        # to cyclic dependencies when astroid tries to resolve
        # what io.BufferedReader is. The code that handles this
        # is in astroid.raw_building.imported_member, which verifies
        # the true name of the module.
        builder = AstroidBuilder()
        module = builder.inspect_build(_io)
        buffered_reader = module.getattr("BufferedReader")[0]
        self.assertEqual(buffered_reader.root().name, "io")


if __name__ == "__main__":
    unittest.main()
