#!/usr/bin/env python

import unittest
import time
from pprint import pprint

import otterwiki.util

class TestUtil(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_serialize_deserialize(self):
        s_i = "kdfjlhg gdklfjghdf gkl;djshfg dgf;lkjhs glkshjad\n"
        salt = "xAxAx"
        # serialize
        s_s = otterwiki.util.serialize(s_i, salt)
        # deserialize
        s_o = otterwiki.util.deserialize(s_s, salt)
        # check if equal
        self.assertEqual(s_i, s_o)
        # check if signature expires
        with self.assertRaises(otterwiki.util.SerializeError):
            otterwiki.util.deserialize(s_s, salt, max_age=-1)
        # check if error is raised
        with self.assertRaises(otterwiki.util.SerializeError):
            otterwiki.util.deserialize(s_s)
        with self.assertRaises(otterwiki.util.SerializeError):
            otterwiki.util.deserialize(s_i)

    def test_get_filename_pagename(self):
        pn = "Testabc"
        fn = "testabc.md"
        self.assertEqual( otterwiki.util.get_pagename(fn), pn )
        self.assertEqual( otterwiki.util.get_filename(pn), fn )
        self.assertEqual( otterwiki.util.get_pagename(otterwiki.util.get_filename(pn)), pn )

    def test_sizeof(self):
        self.assertEqual( otterwiki.util.sizeof_fmt(16384), "16.0KiB" )
        self.assertEqual( otterwiki.util.sizeof_fmt(7812896), "7.5MiB" )


