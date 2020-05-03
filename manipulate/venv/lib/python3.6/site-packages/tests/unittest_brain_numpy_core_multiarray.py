# -*- encoding=utf-8 -*-
# Copyright (c) 2019 hippo91 <guillaume.peillex@gmail.com>
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


@unittest.skipUnless(HAS_NUMPY, "This test requires the numpy library.")
class BrainNumpyCoreMultiarrayTest(unittest.TestCase):
    """
    Test the numpy core multiarray brain module
    """

    numpy_functions_returning_array = (
        ("array", "[1, 2]"),
        ("bincount", "[1, 2]"),
        ("busday_count", "('2011-01', '2011-02')"),
        ("busday_offset", "'2012-03', -1, roll='forward'"),
        ("concatenate", "([1, 2], [1, 2])"),
        ("datetime_as_string", "['2012-02', '2012-03']"),
        ("dot", "[1, 2]", "[1, 2]"),
        ("empty_like", "[1, 2]"),
        ("inner", "[1, 2]", "[1, 2]"),
        ("is_busday", "['2011-07-01', '2011-07-02', '2011-07-18']"),
        ("lexsort", "(('toto', 'tutu'), ('riri', 'fifi'))"),
        ("packbits", "np.array([1, 2])"),
        ("ravel_multi_index", "np.array([[1, 2], [2, 1]])", "(3, 4)"),
        ("unpackbits", "np.array([[1], [2], [3]], dtype=np.uint8)"),
        ("vdot", "[1, 2]", "[1, 2]"),
        ("where", "[True, False]", "[1, 2]", "[2, 1]"),
        ("empty", "[1, 2]"),
        ("zeros", "[1, 2]"),
    )

    numpy_functions_returning_bool = (
        ("can_cast", "np.int32, np.int64"),
        ("may_share_memory", "np.array([1, 2])", "np.array([3, 4])"),
        ("shares_memory", "np.array([1, 2])", "np.array([3, 4])"),
    )

    numpy_functions_returning_dtype = (
        # ("min_scalar_type", "10"),  # Not yet tested as it returns np.dtype
        # ("result_type", "'i4'", "'c8'"),  # Not yet tested as it returns np.dtype
    )

    numpy_functions_returning_none = (("copyto", "([1, 2], [1, 3])"),)

    numpy_functions_returning_tuple = (
        (
            "unravel_index",
            "[22, 33, 44]",
            "(6, 7)",
        ),  # Not yet tested as is returns a tuple
    )

    def _inferred_numpy_func_call(self, func_name, *func_args):
        node = builder.extract_node(
            """
        import numpy as np
        func = np.{:s}
        func({:s})
        """.format(
                func_name, ",".join(func_args)
            )
        )
        return node.infer()

    def test_numpy_function_calls_inferred_as_ndarray(self):
        """
        Test that calls to numpy functions are inferred as numpy.ndarray
        """
        for func_ in self.numpy_functions_returning_array:
            with self.subTest(typ=func_):
                inferred_values = list(self._inferred_numpy_func_call(*func_))
                self.assertTrue(
                    len(inferred_values) == 1,
                    msg="Too much inferred values ({}) for {:s}".format(
                        inferred_values, func_[0]
                    ),
                )
                self.assertTrue(
                    inferred_values[-1].pytype() == ".ndarray",
                    msg="Illicit type for {:s} ({})".format(
                        func_[0], inferred_values[-1].pytype()
                    ),
                )

    def test_numpy_function_calls_inferred_as_bool(self):
        """
        Test that calls to numpy functions are inferred as bool
        """
        for func_ in self.numpy_functions_returning_bool:
            with self.subTest(typ=func_):
                inferred_values = list(self._inferred_numpy_func_call(*func_))
                self.assertTrue(
                    len(inferred_values) == 1,
                    msg="Too much inferred values ({}) for {:s}".format(
                        inferred_values, func_[0]
                    ),
                )
                self.assertTrue(
                    inferred_values[-1].pytype() == "builtins.bool",
                    msg="Illicit type for {:s} ({})".format(
                        func_[0], inferred_values[-1].pytype()
                    ),
                )

    def test_numpy_function_calls_inferred_as_dtype(self):
        """
        Test that calls to numpy functions are inferred as numpy.dtype
        """
        for func_ in self.numpy_functions_returning_dtype:
            with self.subTest(typ=func_):
                inferred_values = list(self._inferred_numpy_func_call(*func_))
                self.assertTrue(
                    len(inferred_values) == 1,
                    msg="Too much inferred values ({}) for {:s}".format(
                        inferred_values, func_[0]
                    ),
                )
                self.assertTrue(
                    inferred_values[-1].pytype() == "numpy.dtype",
                    msg="Illicit type for {:s} ({})".format(
                        func_[0], inferred_values[-1].pytype()
                    ),
                )

    def test_numpy_function_calls_inferred_as_none(self):
        """
        Test that calls to numpy functions are inferred as None
        """
        for func_ in self.numpy_functions_returning_none:
            with self.subTest(typ=func_):
                inferred_values = list(self._inferred_numpy_func_call(*func_))
                self.assertTrue(
                    len(inferred_values) == 1,
                    msg="Too much inferred values ({}) for {:s}".format(
                        inferred_values, func_[0]
                    ),
                )
                self.assertTrue(
                    inferred_values[-1].pytype() == "builtins.NoneType",
                    msg="Illicit type for {:s} ({})".format(
                        func_[0], inferred_values[-1].pytype()
                    ),
                )

    def test_numpy_function_calls_inferred_as_tuple(self):
        """
        Test that calls to numpy functions are inferred as tuple
        """
        for func_ in self.numpy_functions_returning_tuple:
            with self.subTest(typ=func_):
                inferred_values = list(self._inferred_numpy_func_call(*func_))
                self.assertTrue(
                    len(inferred_values) == 1,
                    msg="Too much inferred values ({}) for {:s}".format(
                        inferred_values, func_[0]
                    ),
                )
                self.assertTrue(
                    inferred_values[-1].pytype() == "builtins.tuple",
                    msg="Illicit type for {:s} ({})".format(
                        func_[0], inferred_values[-1].pytype()
                    ),
                )


if __name__ == "__main__":
    unittest.main()
