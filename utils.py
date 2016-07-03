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

Miscelaneous utilities for handling RMPyL programs.

@author: Pedro Santana (psantana@mit.edu).
"""
#from .defs import StateVariable
from .rmpylexceptions import InvalidTypeError

def valid_assignment(assignment):
    """
    Checks if an assignment to state variables is valid.
    """
    if not isinstance(assignment,dict):
        return False
    else:
        for svar,val in assignment.items():
            if not svar.in_domain(val):
                return False
            # if (not isinstance(svar,StateVariable)) or (not svar.in_domain(val)):
            #     return False
        return True

def valid_probability_distribution(distribution):
    """
    Checks if the provided distribution parameters are in the correct format.
    """
    if isinstance(distribution,dict) and 'type' in distribution:
        if distribution['type']=='gaussian':
            if ('mean' in distribution) and ('variance' in distribution) and (distribution['variance']>=0.0):
                return True
        elif distribution['type']=='uniform' or distribution['type']=='unknown_bounded':
            if ('lb' in distribution) and ('ub' in distribution) and (distribution['lb']<=distribution['ub']):
                return True
        else:
            pass

    error_msg='\nERROR: Probability distributions should be specified as dictionaries.\n'
    error_msg+='Available types: gaussian, uniform, unknown_bounded.\n'
    error_msg+='\tGaussian parameters: mean and variance (variance >=0).\n'
    error_msg+='\tUniform: lb and ub (lb<=ub).\n'
    error_msg+='\tUnknown bounded: lb and ub (lb<=ub).\n'
    print(error_msg)
    raise InvalidTypeError('Invalid probability distribution')

def sort_dictionary(in_dict,by_key=True):
    """
    Sorts a dictionary by keys or values.
    """
    return sorted(in_dict.items(),key=lambda x:x[0 if by_key else 1])
