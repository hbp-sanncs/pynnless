#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   PyNNLess -- Yet Another PyNN Abstraction Layer
#   Copyright (C) 2015 Andreas Stöckel
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Reader of the binnf serialisation format. Note that this format is not
standardised and always in sync with the corresponding implementation in CppNAM.
"""

import os
import struct

import numpy as np

# Numbers and constants defining the serialisation format

BLOCK_START_SEQUENCE = 0x4b636c42;
BLOCK_END_SEQUENCE = 0x426c634b;
BLOCK_TYPE_MATRIX = 0x01;

TYPE_INT = 0x00;
TYPE_FLOAT = 0x01;
TYPE_MAP = {
    TYPE_INT: "int32",
    TYPE_FLOAT: "float32"
}

# Helper functions used to determine the length of a storage block

MAX_STR_SIZE = 1024;
BLOCK_TYPE_LEN = 4
SIZE_LEN = 4
TYPE_LEN = 4
NUMBER_LEN = 4

def _str_len(s):
    return SIZE_LEN + len(s)

def _header_len(header):
    res = SIZE_LEN
    for elem in header:
        res += _str_len(elem["name"]) + TYPE_LEN
    return res;

def _matrix_len(matrix):
    return 2 * SIZE_LEN + matrix.size * matrix.dtype.itemsize

def _block_len(name, header, matrix):
    return (BLOCK_TYPE_LEN + _str_len(name) + _header_len(header)
            + _matrix_len(matrix))

def _write_int(fd, i):
    fd.write(struct.pack("i", i))

def _write_str(fd, s):
    if (len(s) > MAX_STR_SIZE):
        raise Exception("String exceeds string size limit of " + MAX_STR_SIZE
                + " bytes.")
    fd.write(struct.pack("i", len(s)))
    fd.write(s)

def _synchronise(fd, marker):
    sync = 0
    while True:
        c = fd.read(1)
        if not c:
            raise Exception("Unexpected end of file")
        sync = (sync >> 8) | (ord(c[0]) << 24)
        if sync == marker:
            return True

def _read_int(fd):
    data = fd.read(4)
    if not data:
        raise Exception("Unexpected end of file")
    return struct.unpack("i", data)[0]

def _read_str(fd):
    data = fd.read(_read_int(fd))
    if not data:
        raise Exception("Unexpected end of file")
    return data

def _tell(fd):
    """
    Returns the current cursor position within the given file descriptor.
    Implements the C++ behaviour of iostream::tellg(). Returns -1 if the feature
    is not implemented (e.g. because we're reading from a stream).
    """
    try:
        return fd.tell()
    except:
        return -1

def header_to_dtype(header):
    return map(lambda x: (x["name"], TYPE_MAP[x["type"]]), header)

def serialise(fd, name, header, matrix):
    """
    Serialises a binnf data block.

    :param name: is the data block name
    :param header: is the data block header
    :param matrix: matrix containing the data that should be serialised
    """

    # Write the block header
    _write_int(fd, BLOCK_START_SEQUENCE)
    _write_int(fd, _block_len(name, header, matrix))
    _write_int(fd, BLOCK_TYPE_MATRIX)

    # Write the name string
    _write_str(fd, name)

    # Write the data header
    _write_int(fd, len(header))
    for i in xrange(len(header)):
        _write_str(fd, header[i]["name"])
        _write_int(fd, header[i]["type"])

    # Write the matrix data
    rows = matrix.shape[0]
    if (len(matrix.shape) == 1):
        cols = len(matrix.dtype.descr)
    else:
        cols = matrix.shape[1]

    if cols != len(header):
        raise Exception("Disecrepancy between matrix number of columns and header")

    _write_int(fd, rows)
    _write_int(fd, cols)
    fd.write(matrix.tobytes())

    # Finalise the block
    _write_int(fd, BLOCK_END_SEQUENCE)

def deseralise(fd):
    name = ""
    header = []
    matrix = None

    # Read some meta-information
    _synchronise(fd, BLOCK_START_SEQUENCE)
    block_len = _read_int(fd)
    pos0 = _tell(fd)

    block_type = _read_int(fd)
    if block_type != BLOCK_TYPE_MATRIX:
        raise Exception("Unexpected block type")

    # Read the name
    name = _read_str(fd)

    # Read the header
    header_len = _read_int(fd)
    header = map(lambda _: {"name": "", "type": TYPE_INT},
            xrange(header_len))
    for i in xrange(header_len):
        header[i]["name"] = _read_str(fd)
        header[i]["type"] = _read_int(fd)

    # Read the data
    rows = _read_int(fd)
    cols = _read_int(fd)
    if (cols != len(header)):
        raise Exception("Disecrepancy between matrix number of columns and header")

    fmt = header_to_dtype(header)
    matrix = np.frombuffer(buffer(fd.read(rows * cols * NUMBER_LEN)), dtype=fmt)

    # Make sure the block size was correct
    pos1 = _tell(fd)
    if pos0 >= 0 and pos1 >= 0 and pos1 - pos0 != block_len:
        raise Exception("Invalid block length")

    # Make sure the end of the block is reached
    block_end = _read_int(fd)
    if block_end != BLOCK_END_SEQUENCE:
        raise Exception("Block end sequence not found")

    return name, header, matrix

