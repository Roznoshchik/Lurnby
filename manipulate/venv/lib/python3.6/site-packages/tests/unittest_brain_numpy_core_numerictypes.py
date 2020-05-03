# -*- encoding=utf-8 -*-
# Copyright (c) 2017-2020 hippo91 <guillaume.peillex@gmail.com>
# Copyright (c) 2017-2018 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2019 Ashley Whetter <ashley@awhetter.co.uk>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER
import unittest

try:
    import numpy  # pylint: disable=unused-import

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from astroid import builder
from astroid import nodes


@unittest.skipUnless(HAS_NUMPY, "This test requires the numpy library.")
class NumpyBrainCoreNumericTypesTest(unittest.TestCase):
    """
    Test of all the missing types defined in numerictypes module.
    """

    all_types = [
        "uint16",
        "uint32",
        "uint64",
        "float16",
        "float32",
        "float64",
        "float96",
        "complex64",
        "complex128",
        "complex192",
        "timedelta64",
        "datetime64",
        "unicode_",
        "str_",
        "bool_",
        "bool8",
        "byte",
        "int8",
        "bytes0",
        "bytes_",
        "cdouble",
        "cfloat",
        "character",
        "clongdouble",
        "clongfloat",
        "complexfloating",
        "csingle",
        "double",
        "flexible",
        "floating",
        "half",
        "inexact",
        "int0",
        "longcomplex",
        "longdouble",
        "longfloat",
        "short",
        "signedinteger",
        "single",
        "singlecomplex",
        "str0",
        "ubyte",
        "uint",
        "uint0",
        "uintc",
        "uintp",
        "ulonglong",
        "unsignedinteger",
        "ushort",
        "void0",
    ]

    def _inferred_numpy_attribute(self, attrib):
        node = builder.extract_node(
            """
        import numpy.core.numerictypes as tested_module
        missing_type = tested_module.{:s}""".format(
                attrib
            )
        )
        return next(node.value.infer())

    def test_numpy_core_types(self):
        """
        Test that all defined types have ClassDef type.
        """
        for typ in self.all_types:
            with self.subTest(typ=typ):
                inferred = self._inferred_numpy_attribute(typ)
                self.assertIsInstance(inferred, nodes.ClassDef)

    def test_generic_types_have_methods(self):
        """
        Test that all generic derived types have specified methods
        """
        generic_methods = [
            "all",
            "any",
            "argmax",
            "argmin",
            "argsort",
            "astype",
            "base",
            "byteswap",
            "choose",
            "clip",
            "compress",
            "conj",
            "conjugate",
            "copy",
            "cumprod",
            "cumsum",
            "data",
            "diagonal",
            "dtype",
            "dump",
            "dumps",
            "fill",
            "flags",
            "flat",
            "flatten",
            "getfield",
            "imag",
            "item",
            "itemset",
            "itemsize",
            "max",
            "mean",
            "min",
            "nbytes",
            "ndim",
            "newbyteorder",
            "nonzero",
            "prod",
            "ptp",
            "put",
            "ravel",
            "real",
            "repeat",
            "reshape",
            "resize",
            "round",
            "searchsorted",
            "setfield",
            "setflags",
            "shape",
            "size",
            "sort",
            "squeeze",
            "std",
            "strides",
            "sum",
            "swapaxes",
            "take",
            "tobytes",
            "tofile",
            "tolist",
            "tostring",
            "trace",
            "transpose",
            "var",
            "view",
        ]

        for type_ in (
            "bool_",
            "bytes_",
            "character",
            "complex128",
            "complex192",
            "complex64",
            "complexfloating",
            "datetime64",
            "flexible",
            "float16",
            "float32",
            "float64",
            "float96",
            "floating",
            "generic",
            "inexact",
            "int16",
            "int32",
            "int32",
            "int64",
            "int8",
            "integer",
            "number",
            "signedinteger",
            "str_",
            "timedelta64",
            "uint16",
            "uint32",
            "uint32",
            "uint64",
            "uint8",
            "unsignedinteger",
            "void",
        ):
            with self.subTest(typ=type_):
                inferred = self._inferred_numpy_attribute(type_)
                for meth in generic_methods:
                    with self.subTest(meth=meth):
                        self.assertTrue(meth in {m.name for m in inferred.methods()})

    def test_generic_types_have_attributes(self):
        """
        Test that all generic derived types have specified attributes
        """
        generic_attr = [
            "base",
            "data",
            "dtype",
            "flags",
            "flat",
            "imag",
            "itemsize",
            "nbytes",
            "ndim",
            "real",
            "size",
            "strides",
        ]

        for type_ in (
            "bool_",
            "bytes_",
            "character",
            "complex128",
            "complex192",
            "complex64",
            "complexfloating",
            "datetime64",
            "flexible",
            "float16",
            "float32",
            "float64",
            "float96",
            "floating",
            "generic",
            "inexact",
            "int16",
            "int32",
            "int32",
            "int64",
            "int8",
            "integer",
            "number",
            "signedinteger",
            "str_",
            "timedelta64",
            "uint16",
            "uint32",
            "uint32",
            "uint64",
            "uint8",
            "unsignedinteger",
            "void",
        ):
            with self.subTest(typ=type_):
                inferred = self._inferred_numpy_attribute(type_)
                for attr in generic_attr:
                    with self.subTest(attr=attr):
                        self.assertNotEqual(len(inferred.getattr(attr)), 0)

    def test_number_types_have_unary_operators(self):
        """
        Test that number types have unary operators
        """
        unary_ops = ("__neg__",)

        for type_ in (
            "float64",
            "float96",
            "floating",
            "int16",
            "int32",
            "int32",
            "int64",
            "int8",
            "integer",
            "number",
            "signedinteger",
            "uint16",
            "uint32",
            "uint32",
            "uint64",
            "uint8",
            "unsignedinteger",
        ):
            with self.subTest(typ=type_):
                inferred = self._inferred_numpy_attribute(type_)
                for attr in unary_ops:
                    with self.subTest(attr=attr):
                        self.assertNotEqual(len(inferred.getattr(attr)), 0)

    def test_array_types_have_unary_operators(self):
        """
        Test that array types have unary operators
        """
        unary_ops = ("__neg__", "__invert__")

        for type_ in ("ndarray",):
            with self.subTest(typ=type_):
                inferred = self._inferred_numpy_attribute(type_)
                for attr in unary_ops:
                    with self.subTest(attr=attr):
                        self.assertNotEqual(len(inferred.getattr(attr)), 0)

    def test_datetime_astype_return(self):
        """
        Test that the return of astype method of the datetime object
        is inferred as a ndarray.

        PyCQA/pylint#3332
        """
        node = builder.extract_node(
            """
        import numpy as np
        import datetime
        test_array = np.datetime64(1, 'us')
        test_array.astype(datetime.datetime)
        """
        )
        licit_array_types = ".ndarray"
        inferred_values = list(node.infer())
        self.assertTrue(
            len(inferred_values) == 1,
            msg="Too much inferred value for {:s}".format("datetime64.astype"),
        )
        self.assertTrue(
            inferred_values[-1].pytype() in licit_array_types,
            msg="Illicit type for {:s} ({})".format(
                "datetime64.astype", inferred_values[-1].pytype()
            ),
        )


if __name__ == "__main__":
    unittest.main()
