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

Module defining different types of RMPyL constraints.

@author: Pedro Santana (psantana@mit.edu).
"""
from .defs import ConditionalElement,StateVariable
from .utils import valid_probability_distribution
from .rmpylexceptions import InvalidTypeError,MissingArgumentError

class RMPyLConstraint(ConditionalElement):
    """Base class for representing RMPyL constraints."""
    def __init__(self,ctype,**kwargs):
        super(RMPyLConstraint,self).__init__(**kwargs)
        self.type = ctype

    @property
    def type(self):
        """Constraint type."""
        return self.properties['type']

    @type.setter
    def type(self,new_type):
        self.properties['type'] = new_type

class TemporalConstraint(RMPyLConstraint):
    """Class representing temporal constraints."""
    def __init__(self,start,end,ctype,**kwargs):
        super(TemporalConstraint,self).__init__(ctype,**kwargs)
        self.properties['start'] = start
        self.properties['end'] = end

        _available_types = ['controllable','uncontrollable_bounded','uncontrollable_probabilistic']
        if not (ctype in _available_types):
            raise InvalidTypeError('Temporal constraints should have a type in '+str(_available_types))

        #Simple temporal constraints (STC) and STC with set-bounded uncertainty
        #(STCU) both have a upper and lower bound
        if self.type in ['controllable','uncontrollable_bounded']:
            if ('lb' in kwargs) and ('ub' in kwargs):
                if self.type == 'controllable':
                    self.set_stc(kwargs['lb'],kwargs['ub'])
                else:
                    self.set_stcu(kwargs['lb'],kwargs['ub'])
            else:
                raise MissingArgumentError('STCs and STCUs must have have lb and ub specified.')
        #Probabilistic simple temporal constraints (PSTC) have a distribution
        #parameter, rather than an upper and lower bound.
        else:
            #Example distribution = {'type':'uniform','lb':0.0,'ub':1.0}
            if ('distribution' in kwargs):
                self.set_pstc(kwargs['distribution'])
            else:
                raise MissingArgumentError('PSTCs must have an associated distribution argument.')

        #Makes the support for the temporal constraint be consistent with the
        #support of its start and end events.        
        self.support_AND(self.start.support)
        self.support_AND(self.end.support)

    @property
    def start(self):
        """Start event of temporal constraint."""
        return self.properties['start']

    @start.setter
    def start(self,new_start):
        """Sets the start event."""
        self.properties['start'] = new_start

    @property
    def end(self):
        """End event of temporal constraint."""
        return self.properties['end']

    @end.setter
    def end(self,new_end):
        """Sets the end event."""
        self.properties['end'] = new_end

    @property
    def lb(self):
        """
        Lower bound for set-bounded temporal constraints (STC and STCU)
        """
        return self.bounds[0]

    @property
    def ub(self):
        """
        Upper bound for set-bounded temporal constraints (STC and STCU)
        """
        return self.bounds[1]

    @property
    def bounds(self):
        """
        Upper and lower bounds for a temporal constraint.
        """
        return self._bounds

    @bounds.setter
    def bounds(self,new_bounds):
        """
        Sets new bounds Upper and lower bounds for a temporal constraint.
        """
        if new_bounds[0]<=new_bounds[1]:
            self._bounds = new_bounds
        else:
            raise InvalidTypeError('Temporal constraints must have have lb and ub such that lb<=ub.')

    @property
    def distribution(self):
        """
        Distribution for probabilistic temporal constraints (PSTC)
        """
        return self._distribution

    @distribution.setter
    def distribution(self,new_distribution):
        if new_distribution == None:
            self._distribution = None
        elif valid_probability_distribution(new_distribution):
            self._distribution = new_distribution
            lb  = new_distribution['lb'] if 'lb' in new_distribution else -float('inf')
            ub = new_distribution['ub'] if 'ub' in new_distribution else float('inf')
            self.bounds = (lb,ub)
        else:
            raise InvalidTypeError('Invalid probability distribution.')

    def set_stc(self,lb,ub):
        """
        Sets a Simple Temporal Constraint (STC)
        """
        self.type = 'controllable'
        self.distribution = None
        self.bounds = (lb,ub)

    def set_stcu(self,lb,ub):
        """
        Sets a Simple Temporal Constraint with Uncertainty (STCU)
        """
        self.type = 'uncontrollable_bounded'
        self.distribution={'type':'unknown_bounded','lb':lb,'ub':ub}

    def set_pstc(self,distribution):
        """
        Sets a Probabilistic Simple Temporal Constraint (PSTC)
        """
        self.type = 'uncontrollable_probabilistic'
        self.distribution= distribution

    #This function should be migrated to __eq__ somehow
    def is_equivalent(self,other):
        """
        Two temporal constraints will be equal if they constraint the same
        events in the same way.
        """
        return self.constraint_same_events(other) and \
               (self.distribution == other.distribution) and \
               (self.lb == other.lb) and (self.ub == other.ub)

    def constraint_same_events(self,other):
        """
        Whether two temporal constraints constraint the same pair of events
        """
        return ((self.start.name == other.start.name) or (self.start.id == other.start.id)) and \
               ((self.end.name == other.end.name) or (self.end.id == other.end.id)) and \
               (self.type == other.type) and (self.support == other.support)

    def __repr__(self):
        str_prop = '' if len(self.properties)==0 else str(self.properties)
        return 'TempConst(at 0x%x) '%(id(self))+str_prop


class ChanceConstraint(RMPyLConstraint):
    """Class representing temporal constraints."""
    def __init__(self,constraint_scope,risk,**kwargs):
        super(ChanceConstraint,self).__init__('chance',**kwargs)
        self.risk = risk
        self.constraints=constraint_scope

    @property
    def risk(self):
        """
        Maximum risk allowed by this chance constraint.
        """
        return self.properties['risk']

    @risk.setter
    def risk(self,new_risk):
        """
        Checks if a meaningful value of risk has been provided and updates the
        risk for the chance constraint.
        """
        if (new_risk<0.0) or (new_risk>1.0):
            raise ValueError('Chance constraint risk must be a valid probability.')
        self.properties['risk'] = new_risk

    @property
    def constraints(self):
        """
        Returns the constraints over which this chance constraint is defined.
        """
        return self.properties['constraints']

    @constraints.setter
    def constraints(self,constraint_scope):
        """
        Checks if the chance constraint is defined over a valid list of RMPyLConstraint
        objects and sets them, if yes.
        """
        for const in constraint_scope:
            if not isinstance(const,RMPyLConstraint):
                raise TypeError('Chance constraints should be defined over RMPyLConstraint instances.')
        self.properties['constraints']=constraint_scope

    def __repr__(self):
        str_prop = '' if len(self.properties)==0 else str(self.properties)
        return 'ChanceConst(at 0x%x) '%(id(self))+str_prop


class StateConstraint(RMPyLConstraint):
    """Base class for representing state constraints."""
    def __init__(self,scope,**kwargs):
        super(StateConstraint,self).__init__('state',**kwargs)
        for var in scope:
            if not isinstance(var,StateVariable):
                raise TypeError('Scope must be a list of state variables.')
        self.properties['scope']=scope

    @property
    def scope(self):
        """State variables involved in the constraint."""
        return self.properties['scope']

    def __repr__(self):
        str_prop = '' if len(self.properties)==0 else str(self.properties)
        return 'StateConst(at 0x%x) '%(id(self))+str_prop


class AssignmentStateConstraint(StateConstraint):
    """Class representing an assignment constraint on state variables."""
    def __init__(self,scope,values,**kwargs):
        super(AssignmentStateConstraint,self).__init__(scope,**kwargs)

        if len(scope)!=len(values):
            raise TypeError('Scope and values must have the same length.')

        for i,val in enumerate(values):
            if not scope[i].in_domain(val):
                raise ValueError('Assignments should be contained in the domain of a state variable.')

        self.properties['values']=values #Variable coefficients

    @property
    def values(self):
        """Values assigned to variables in scope."""
        return self.properties['values']

    @property
    def as_string(self):
        """
        Convenient string representation of an assignment constraint
        """
        str_prop = ''
        for svar,val in zip(self.scope,self.values):
            str_prop+='%s=%s '%(svar.name,str(val))
        return str_prop

    def __repr__(self):
        return 'AssignmentStateConstraint(at 0x%x) '%(id(self))+self.as_string


class LinearStateConstraint(StateConstraint):
    """Class representing a linear constraint on state variables."""
    def __init__(self,scope,coef,rel,rhs,**kwargs):
        super(LinearStateConstraint,self).__init__(scope,**kwargs)
        self.properties['coef']=coef #Variable coefficients

        if len(scope)!=len(coef):
            raise TypeError('Scope and coefficients must have the same length.')

        for val in coef+[rhs]:
            if not isinstance(val,(int,float)):
                raise TypeError('Coefficients and RHS must be integers or floats.')

        _linear_rel=['<','<=','=','>','>=']
        if rel in _linear_rel:
            self.properties['rel']=rel #Relationship
        else:
            raise TypeError('Relationship must be in '+str(_linear_rel))

        self.properties['rhs']=rhs #Right-hand side

    @property
    def coef(self):
        """Coefficients of the linear constraint."""
        return self.properties['coef']

    @property
    def rel(self):
        """Relationship in the linear inequality."""
        return self.properties['rel']

    @property
    def rhs(self):
        """Right-hand side of the linear inequality."""
        return self.properties['rhs']

    @property
    def as_string(self):
        str_prop = ''
        for svar,co in zip(self.scope,self.coef):
            str_prop+='%s%s*%s'%('-' if co<0 else '+',abs(co),svar.name)
        str_prop+=' '+self.rel+' '+str(self.rhs)
        return str_prop

    def __repr__(self):
        return 'LinearStateConstraint(at 0x%x) '%(id(self))+self.as_string
