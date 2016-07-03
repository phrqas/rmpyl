#!/usr/bin/env python
#
#  A Python package for writing RMPL programs.
#
#  Copyright (c) 2015 MIT. All rights reserved.
#
#   author: Pedro Santana
#   e-mail: psantana@mit.edu
#   website: people.csail.mit.edu/psantana
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#  3. Neither the name(s) of the copyright holders nor the names of its
#     contributors or of the Massachusetts Institute of Technology may be
#     used to endorse or promote products derived from this software
#     without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
#  OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
#  AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
#  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
"""
RMPyL: a Python package for writing RMPL programs.

Module defining the exceptions thrown by the language.

@author: Pedro Santana (psantana@mit.edu).
"""
class RMPyLException(Exception):
    """Base class for RMPyL exceptions."""
    def __init__(self,value):
        self.value=value      
    def __str__(self):
        return repr(self.value)        

class MissingArgumentError(RMPyLException):
    """Raised when a missing argument is detected."""
    pass

class InvalidTypeError(RMPyLException):
    """Raised when an invalid type for an RMPyL element is chosen."""
    pass

class InvalidValueError(RMPyLException):
    """Raised when an invalid value for an RMPyL parameter element is chosen."""
    pass

class IDError(RMPyLException):
    """Raised when there is a problem with an element's ID."""
    pass

class CompositionError(RMPyLException):
    """Raised when there is a problem with a composition of episodes."""
    pass

class DuplicateElementError(RMPyLException):
    """Raised when there a duplicate element is detected in the program."""
    pass

class InconsistentSupportError(RMPyLException):
    """Raised when two supports are jointly inconsistent (empty intersection)."""
    def __init__(self,value,*assignments): 
        super(InconsistentSupportError,self).__init__(value)        
        self.assignments=assignments  


