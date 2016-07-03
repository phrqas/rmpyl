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

Module defining basic RMPyL elements.

@author: Pedro Santana (psantana@mit.edu).
"""
from collections import namedtuple
from .rmpylexceptions import InvalidTypeError,InconsistentSupportError,MissingArgumentError


class NamedElement(object):
    """
    Class representing elements that have a name, unique ID, and store their
    properties as a dictionary.
    """
    def __init__(self,**kwargs):
        #User-defined ID
        if 'id' in kwargs:
            self.id = kwargs['id']
            del kwargs['id'] #Remove ID from properties
        #If no ID is provided, gives it a unique default value
        else:
            self.id = self.__class__.__name__+'_0x%x'%(id(self))

        #User-defined name
        if 'name' in kwargs:
            self.name = kwargs['name']
            del kwargs['name'] #Remove name from properties
        #If no name is provided, gives it a default one
        else:
            self.name = '_'+self.id

        #Stores the rest of the properties (and rehashes)
        self.properties = kwargs

    @property
    def id(self):
        """Unique object ID."""
        return self._id

    @id.setter
    def id(self,new_id):
        self._id = new_id

    @property
    def name(self):
        """Element's name (does not have to be unique)."""
        return self._name
    @name.setter
    def name(self,new_name):
        self._name = new_name

    @property
    def properties(self):
        """Property dictionary."""
        return self._properties

    @properties.setter
    def properties(self,new_properties):
        self._properties = new_properties


class ConditionalElement(NamedElement):
    """
    Class representing elements in a temporal plan with choice that depend
    on assignments to choices. A support is represented in Disjunctive Normal
    Form (DNF), i.e., it is a disjunction (OR) of conjunctions (AND) represented
    as a list of lists.
    """
    def __init__(self,**kwargs):
        super(ConditionalElement,self).__init__(**kwargs)

        #List of choice assignments supporting the activation of this element
        self.clear_support()

    @property
    def support(self):
        """
        List of choice assignments representing the support of this element.
        """
        return self.properties['support']

    @support.setter
    def support(self,new_support):
        """
        Sets a new DNF support for the element.
        """
        self.properties['support'] = new_support

        #Updates the sets of controllable and uncontrollable choices
        self._support_dict={'decisions':[],'observations':[]}
        for conj in new_support:
            decisions=[];observations=[]
            for assig in conj:
                if assig.var.type=='controllable':
                    decisions.append(assig.var)
                else:
                    observations.append(assig.var)
            #For each conjunction,records the sets of controllable and
            #uncontrollable choices.
            self._support_dict['decisions'].append(frozenset(decisions))
            self._support_dict['observations'].append(frozenset(observations))

    @property
    def support_decisions(self):
        """
        Controllable choices (decisions) in the support.
        """
        return self._support_dict['decisions']

    @property
    def support_observations(self):
        """
        Uncontrollable choices (observations) in the support.
        """
        return self._support_dict['observations']

    @property
    def support_variables(self):
        """
        All support variables.
        """
        return frozenset(self.support_decisions+self.support_observations)

    def copy_support(self):
        """
        Returns a copy of the support.
        """
        return set([frozenset(conj) for conj in self.support])

    def clear_support(self):
        """Clears the element's support (always true)."""
        self.support = set([frozenset()])

    def add_support_assignment(self,assignment):
        """Adds a choice assignment to the element's DNF support."""
        new_support=set()
        for conj in self.support:
            new_support.add(conj|{assignment})
        self.support = new_support

    def set_disjunction(self,disjunction):
        """
        Sets the support as a disjunction of conjunctions.
        """
        self.support = set([frozenset(conj) for conj in disjunction])

    def set_conjunction(self,assignment_list):
        """
        Sets the support as a single conjunction of assignments.
        """
        self.support = set([frozenset(assignment_list)])

    def support_AND(self,other_support):
        """
        Sets the support as the Cartesian product (AND) of the current support and
        the argument.
        """
        new_support= support_conjunction(self.support,other_support)
        if len(new_support)==0:
            raise InconsistentSupportError('Empty intersection of supports',self.support,other_support)
        else:
            self.support = new_support

    def support_OR(self,other_support):
        """
        Sets the support as the union (OR) of the current support and
        the argument.
        """
        self.support.update(other_support)

    def has_empty_support(self):
        """Returns whether the element has an empty support."""
        return sum([len(conj) for conj in self.support])==0

    def is_active(self,choice_assignments):
        """
        Returns whether the given conjunction of choice assignments (controllable or
        uncontrollable) is a superset of one of the conjunctions composing the
        element's support written in DNF (disjunction of conjunctions).
        """
        for conj in self.support:
            if conj <= choice_assignments:
                return True
        return False

    def is_consistent(self,choice_assignments):
        """
        Returns whether the given conjunction of choice assignments (controllable or
        uncontrollable) could entail one of the conjunctions composing the
        element's support written in DNF (disjunction of conjunctions).
        """
        choice_assig_dict = {a.var:a.value for a in choice_assignments}
        for conj in self.support:
            for assig in conj:
                if (assig.var in choice_assig_dict) and (assig.value!=choice_assig_dict[assig.var]):
                    return False
        return True


class Event(ConditionalElement):
    """
    Class representing a temporal event, and the associated state.
    """
    def __init__(self,**kwargs):
        super(Event,self).__init__(**kwargs)

    def __repr__(self):
        str_prop = '' if len(self.properties)==0 else str(self.properties)
        return 'Event(at 0x%x) '%(id(self))+str_prop


class Choice(Event):
    """
    Class representing a choice event.
    """
    def __init__(self,domain,ctype,**kwargs):
        super(Choice,self).__init__(**kwargs)
        self.domain = domain
        self.type = ctype

    @property
    def domain(self):
        return self.properties['domain']

    @domain.setter
    def domain(self,new_domain):
        self.properties['domain'] = new_domain

    @property
    def type(self):
        return self.properties['type']

    @type.setter
    def type(self,new_type):
        _available_types = ['controllable','uncontrollable','probabilistic']
        if new_type in _available_types:
            self.properties['type'] = new_type
        else:
            raise InvalidTypeError('%s is invalid. Choices must be %s'%(new_type,str(_available_types)))

    @property
    def utility(self):
        return self.properties['utility'] if 'utility' in self.properties else []

    @utility.setter
    def utility(self,new_utilities):
        if len(new_utilities)==len(self.domain):
            self.properties['utility'] = new_utilities
        else:
            raise ValueError('Utilities are not consistent with choice domain.')

    @property
    def probability(self):
        return self.properties['probability'] if 'probability' in self.properties else []

    @probability.setter
    def probability(self,new_probabilities):
        if (len(new_probabilities)==len(self.domain)) and abs(sum(new_probabilities)-1.0)<1e-5:
            self.properties['probability'] = new_probabilities
        else:
            raise ValueError('Probabilities are not consistent with choice domain or do not sum to one.')

    def __repr__(self):
        str_prop = '' if len(self.properties)==0 else str(self.properties)
        return 'Choice(at 0x%x) '%(id(self))+str_prop


class ChoiceAssignment(namedtuple('ChoiceAssignment',['var','value','negated'])):
    """
    Simple class representing an assignment to a choice event.
    """
    __slots__= ()

    @property
    def utility(self):
        """Utility associated with this assignment"""
        return self.var.utility[self.var.domain.index(self.value)]

    @property
    def probability(self):
        """Probability associated with this assignment"""
        return self.var.probability[self.var.domain.index(self.value)]

    def __repr__(self):
        """Convenient string representation."""
        if self.negated:
            return 'NOT(ChoiceAssignment: %s=%s)' % (self.var.name,self.value)
        else:
            return 'ChoiceAssignment: %s=%s' % (self.var.name,self.value)


class StateVariable(NamedElement):
    """
    Class representing a state variable.
    """
    def __init__(self,domain_dict,**kwargs):
        super(StateVariable,self).__init__(**kwargs)

        if ('type' in domain_dict) and ('domain' in domain_dict):
            _available_types=['finite-discrete','continuous']
            if domain_dict['type'] in _available_types:
                self.properties['type']=domain_dict['type']
                domain = domain_dict['domain']
                if isinstance(domain,list):
                    if self.properties['type']=='continuous':
                        if len(domain_dict['domain'])!=2 or (domain[0]>domain[1]):
                            raise InvalidTypeError('Continuous domains should be specified as [lb ub], where lb <= ub.')
                    self.properties['domain']=domain
                else:
                    raise InvalidTypeError('Domains should be lists.')
            else:
                raise InvalidTypeError('Domain types must be in '+str(_available_types))
        else:
            raise MissingArgumentError('State variable domains must have a type and value keywords.')

    @property
    def type(self):
        return self.properties['type']

    @property
    def domain(self):
        return self.properties['domain']

    def in_domain(self,value):
        """Returns whether a value is contained in the domain of a state variable. """
        if self.type=='finite-discrete':
            return (value in self.domain)
        else:
            lb,ub = self.domain
            return (value>=lb)and(value<=ub)


def consistent_supports(support1,support2):
    """
    Whether two supports are consistent with each other, i.e., they can be
    satisfied at the same time.
    """
    return len(support_conjunction(support1,support2))!=0


def support_conjunction(support1,support2):
    """
    Computes the Cartesian product (AND) of two DNF supports.
    """
    AND_support=set()
    for conj1 in support1:
        for conj2 in support2:
            new_conj = assignment_conjunction(conj1,conj2)
            if new_conj!=None:
                AND_support.add(frozenset(new_conj))

    return AND_support

def support_difference(support1,support2):
    """
    The difference between two sets can be written as
        A-B = A AND NOT(B)

    Therefore, the difference between supports written in DNF can be expressed as
        (C1 OR C2)-(D1 OR D2) = (C1 OR C2) AND (NOT D1 AND NOT D2)
                              = (C1 AND (NOT D1 AND NOT D2)) OR (C2 AND (NOT D1 AND NOT D2))
    Hence, for every conjunction in the first support, one must subtract the all
    other conjunctions from the second support.
    """
    difference_support=[]
    for conj1 in support1:
        diff = conj1
        for conj2 in support2:
            diff = diff-conj2
        difference_support.append(diff)

    return difference_support


def assignment_conjunction(c1,c2): #FIXME: deal with negated assignments
    """
    Computes the intersection of two conjunctions of assignments
    """
    unique = c1.union(c2)#Conjunction without repeated elements
    negated_map={}
    for el1 in unique:
        for el2 in unique:
            if el1 != el2:
                #Assignments related to the same variable
                if el1.var.id==el2.var.id:
                    #Neither is negated
                    if not (el1.negated or el2.negated):
                        if(el1.value!=el2.value):
                            return None #Inconsistent double assignment to a variable
                    #Only one is negated
                    elif (el1.negated and not el2.negated) or (not el1.negated and el2.negated):
                        if(el1.value==el2.value):
                            return None #You can't assign and not assign a value to a variable
                    #Both are negated
                    else:
                        if el1.var in negated_map:
                            negated_map[el1.var]+=1
                        else:
                            negated_map[el1.var]=2

    #You cannot negate all assignments to a variable
    for var,num_negated in negated_map.items():
        if num_negated==len(var.domain):
            return None

    return  unique
