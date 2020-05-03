# -*- coding: utf-8 -*-
# Copyright (c) 2014-2016, 2018-2020 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2014 Google, Inc.
# Copyright (c) 2014 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2015 Florian Bruhin <me@the-compiler.org>
# Copyright (c) 2015 Radosław Ganczarek <radoslaw@ganczarek.in>
# Copyright (c) 2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2018 Mario Corchero <mcorcherojim@bloomberg.net>
# Copyright (c) 2018 Mario Corchero <mariocj89@gmail.com>
# Copyright (c) 2019 Ashley Whetter <ashley@awhetter.co.uk>
# Copyright (c) 2019 Hugo van Kemenade <hugovk@users.noreply.github.com>
# Copyright (c) 2019 markmcclain <markmcclain@users.noreply.github.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

"""
unit tests for module modutils (module manipulation utilities)
"""
import distutils.version
import email
import os
import sys
import unittest
import xml
from xml import etree
from xml.etree import ElementTree
import tempfile
import shutil

import astroid
from astroid.interpreter._import import spec
from astroid import modutils
from . import resources


def _get_file_from_object(obj):
    return modutils._path_from_filename(obj.__file__)


class ModuleFileTest(unittest.TestCase):
    package = "mypypa"

    def tearDown(self):
        for k in list(sys.path_importer_cache):
            if "MyPyPa" in k:
                del sys.path_importer_cache[k]

    def test_find_zipped_module(self):
        found_spec = spec.find_spec(
            [self.package], [resources.find("data/MyPyPa-0.1.0-py2.5.zip")]
        )
        self.assertEqual(found_spec.type, spec.ModuleType.PY_ZIPMODULE)
        self.assertEqual(
            found_spec.location.split(os.sep)[-3:],
            ["data", "MyPyPa-0.1.0-py2.5.zip", self.package],
        )

    def test_find_egg_module(self):
        found_spec = spec.find_spec(
            [self.package], [resources.find("data/MyPyPa-0.1.0-py2.5.egg")]
        )
        self.assertEqual(found_spec.type, spec.ModuleType.PY_ZIPMODULE)
        self.assertEqual(
            found_spec.location.split(os.sep)[-3:],
            ["data", "MyPyPa-0.1.0-py2.5.egg", self.package],
        )

    def test_find_distutils_submodules_in_virtualenv(self):
        found_spec = spec.find_spec(["distutils", "version"])
        self.assertEqual(found_spec.location, distutils.version.__file__)


class LoadModuleFromNameTest(unittest.TestCase):
    """ load a python module from it's name """

    def test_knownValues_load_module_from_name_1(self):
        self.assertEqual(modutils.load_module_from_name("sys"), sys)

    def test_knownValues_load_module_from_name_2(self):
        self.assertEqual(modutils.load_module_from_name("os.path"), os.path)

    def test_raise_load_module_from_name_1(self):
        self.assertRaises(
            ImportError, modutils.load_module_from_name, "os.path", use_sys=0
        )


class GetModulePartTest(unittest.TestCase):
    """given a dotted name return the module part of the name"""

    def test_knownValues_get_module_part_1(self):
        self.assertEqual(
            modutils.get_module_part("astroid.modutils"), "astroid.modutils"
        )

    def test_knownValues_get_module_part_2(self):
        self.assertEqual(
            modutils.get_module_part("astroid.modutils.get_module_part"),
            "astroid.modutils",
        )

    def test_knownValues_get_module_part_3(self):
        """relative import from given file"""
        self.assertEqual(
            modutils.get_module_part("node_classes.AssName", modutils.__file__),
            "node_classes",
        )

    def test_knownValues_get_compiled_module_part(self):
        self.assertEqual(modutils.get_module_part("math.log10"), "math")
        self.assertEqual(modutils.get_module_part("math.log10", __file__), "math")

    def test_knownValues_get_builtin_module_part(self):
        self.assertEqual(modutils.get_module_part("sys.path"), "sys")
        self.assertEqual(modutils.get_module_part("sys.path", "__file__"), "sys")

    def test_get_module_part_exception(self):
        self.assertRaises(
            ImportError, modutils.get_module_part, "unknown.module", modutils.__file__
        )


class ModPathFromFileTest(unittest.TestCase):
    """ given an absolute file path return the python module's path as a list """

    def test_knownValues_modpath_from_file_1(self):
        self.assertEqual(
            modutils.modpath_from_file(ElementTree.__file__),
            ["xml", "etree", "ElementTree"],
        )

    def test_raise_modpath_from_file_Exception(self):
        self.assertRaises(Exception, modutils.modpath_from_file, "/turlututu")

    def test_import_symlink_with_source_outside_of_path(self):
        with tempfile.NamedTemporaryFile() as tmpfile:
            linked_file_name = "symlinked_file.py"
            try:
                os.symlink(tmpfile.name, linked_file_name)
                self.assertEqual(
                    modutils.modpath_from_file(linked_file_name), ["symlinked_file"]
                )
            finally:
                os.remove(linked_file_name)

    def test_import_symlink_both_outside_of_path(self):
        with tempfile.NamedTemporaryFile() as tmpfile:
            linked_file_name = os.path.join(tempfile.gettempdir(), "symlinked_file.py")
            try:
                os.symlink(tmpfile.name, linked_file_name)
                self.assertRaises(
                    ImportError, modutils.modpath_from_file, linked_file_name
                )
            finally:
                os.remove(linked_file_name)

    def test_load_from_module_symlink_on_symlinked_paths_in_syspath(self):
        # constants
        tmp = tempfile.gettempdir()
        deployment_path = os.path.join(tmp, "deployment")
        path_to_include = os.path.join(tmp, "path_to_include")
        real_secret_path = os.path.join(tmp, "secret.py")
        symlink_secret_path = os.path.join(path_to_include, "secret.py")

        # setup double symlink
        # /tmp/deployment
        # /tmp/path_to_include (symlink to /tmp/deployment)
        # /tmp/secret.py
        # /tmp/deployment/secret.py (points to /tmp/secret.py)
        try:
            os.mkdir(deployment_path)
            self.addCleanup(shutil.rmtree, deployment_path)
            os.symlink(deployment_path, path_to_include)
            self.addCleanup(os.remove, path_to_include)
        except OSError:
            pass
        with open(real_secret_path, "w"):
            pass
        os.symlink(real_secret_path, symlink_secret_path)
        self.addCleanup(os.remove, real_secret_path)

        # add the symlinked path to sys.path
        sys.path.append(path_to_include)
        self.addCleanup(sys.path.pop)

        # this should be equivalent to: import secret
        self.assertEqual(modutils.modpath_from_file(symlink_secret_path), ["secret"])


class LoadModuleFromPathTest(resources.SysPathSetup, unittest.TestCase):
    def test_do_not_load_twice(self):
        modutils.load_module_from_modpath(["data", "lmfp", "foo"])
        modutils.load_module_from_modpath(["data", "lmfp"])
        # pylint: disable=no-member; just-once is added by a test file dynamically.
        self.assertEqual(len(sys.just_once), 1)
        del sys.just_once


class FileFromModPathTest(resources.SysPathSetup, unittest.TestCase):
    """given a mod path (i.e. splited module / package name), return the
    corresponding file, giving priority to source file over precompiled file
    if it exists"""

    def test_site_packages(self):
        filename = _get_file_from_object(modutils)
        result = modutils.file_from_modpath(["astroid", "modutils"])
        self.assertEqual(os.path.realpath(result), os.path.realpath(filename))

    def test_std_lib(self):
        path = modutils.file_from_modpath(["os", "path"]).replace(".pyc", ".py")
        self.assertEqual(
            os.path.realpath(path),
            os.path.realpath(os.path.__file__.replace(".pyc", ".py")),
        )

    def test_builtin(self):
        self.assertIsNone(modutils.file_from_modpath(["sys"]))

    def test_unexisting(self):
        self.assertRaises(ImportError, modutils.file_from_modpath, ["turlututu"])

    def test_unicode_in_package_init(self):
        # file_from_modpath should not crash when reading an __init__
        # file with unicode characters.
        modutils.file_from_modpath(["data", "unicode_package", "core"])


class GetSourceFileTest(unittest.TestCase):
    def test(self):
        filename = _get_file_from_object(os.path)
        self.assertEqual(
            modutils.get_source_file(os.path.__file__), os.path.normpath(filename)
        )

    def test_raise(self):
        self.assertRaises(modutils.NoSourceFile, modutils.get_source_file, "whatever")


class StandardLibModuleTest(resources.SysPathSetup, unittest.TestCase):
    """
    return true if the module may be considered as a module from the standard
    library
    """

    def test_datetime(self):
        # This is an interesting example, since datetime, on pypy,
        # is under lib_pypy, rather than the usual Lib directory.
        self.assertTrue(modutils.is_standard_module("datetime"))

    def test_builtins(self):
        self.assertFalse(modutils.is_standard_module("__builtin__"))
        self.assertTrue(modutils.is_standard_module("builtins"))

    def test_builtin(self):
        self.assertTrue(modutils.is_standard_module("sys"))
        self.assertTrue(modutils.is_standard_module("marshal"))

    def test_nonstandard(self):
        self.assertFalse(modutils.is_standard_module("astroid"))

    def test_unknown(self):
        self.assertFalse(modutils.is_standard_module("unknown"))

    def test_4(self):
        self.assertTrue(modutils.is_standard_module("hashlib"))
        self.assertTrue(modutils.is_standard_module("pickle"))
        self.assertTrue(modutils.is_standard_module("email"))
        self.assertTrue(modutils.is_standard_module("io"))
        self.assertFalse(modutils.is_standard_module("StringIO"))
        self.assertTrue(modutils.is_standard_module("unicodedata"))

    def test_custom_path(self):
        datadir = resources.find("")
        if any(datadir.startswith(p) for p in modutils.EXT_LIB_DIRS):
            self.skipTest("known breakage of is_standard_module on installed package")

        self.assertTrue(modutils.is_standard_module("data.module", (datadir,)))
        self.assertTrue(
            modutils.is_standard_module("data.module", (os.path.abspath(datadir),))
        )

    def test_failing_edge_cases(self):
        # using a subpackage/submodule path as std_path argument
        self.assertFalse(modutils.is_standard_module("xml.etree", etree.__path__))
        # using a module + object name as modname argument
        self.assertTrue(modutils.is_standard_module("sys.path"))
        # this is because only the first package/module is considered
        self.assertTrue(modutils.is_standard_module("sys.whatever"))
        self.assertFalse(modutils.is_standard_module("xml.whatever", etree.__path__))


class IsRelativeTest(unittest.TestCase):
    def test_knownValues_is_relative_1(self):
        self.assertTrue(modutils.is_relative("utils", email.__path__[0]))

    def test_knownValues_is_relative_3(self):
        self.assertFalse(modutils.is_relative("astroid", astroid.__path__[0]))


class GetModuleFilesTest(unittest.TestCase):
    def test_get_module_files_1(self):
        package = resources.find("data/find_test")
        modules = set(modutils.get_module_files(package, []))
        expected = [
            "__init__.py",
            "module.py",
            "module2.py",
            "noendingnewline.py",
            "nonregr.py",
        ]
        self.assertEqual(modules, {os.path.join(package, x) for x in expected})

    def test_get_all_files(self):
        """test that list_all returns all Python files from given location
        """
        non_package = resources.find("data/notamodule")
        modules = modutils.get_module_files(non_package, [], list_all=True)
        self.assertEqual(modules, [os.path.join(non_package, "file.py")])

    def test_load_module_set_attribute(self):
        del xml.etree.ElementTree
        del sys.modules["xml.etree.ElementTree"]
        m = modutils.load_module_from_modpath(["xml", "etree", "ElementTree"])
        self.assertTrue(hasattr(xml, "etree"))
        self.assertTrue(hasattr(xml.etree, "ElementTree"))
        self.assertTrue(m is xml.etree.ElementTree)


if __name__ == "__main__":
    unittest.main()
