#!/bin/sh
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

find -depth \(\
		\(\
			   -name "*.backup"\
			-o -name "*~"\
			-o -name "*.pyc"\
			-o -wholename "*examples/reports*"\
			-o -wholename "*examples/application_generated_data*"\
			-o -wholename "*README.html"\
		\) -a \! \(\
			   -wholename "*.git/*"\
			-o -wholename "*.svn" \)\
		\) -delete -print
