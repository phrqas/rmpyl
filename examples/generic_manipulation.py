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

Encoding of the Boeing scenario in RMPyL

@author: Pedro Santana (psantana@mit.edu).
"""
from rmpyl.rmpyl import Episode,StateVariable,InvalidTypeError,valid_assignment
import ipdb

class Object(object):
    """Object that can be manipulated."""
    def __init__(self,name,ob_type,location_names,manipulator_names):
        self.name=name

        _object_types = ['componenttype','cleanertype','soldertype']
        if ob_type in _object_types:
            self.type=ob_type
        else:
            raise InvalidTypeError('Object type must be in '+str(_object_types))
        
        #Model state variables.         
        self.soldered=StateVariable(name=self.name+'-soldered-state',
                                    domain_dict={'type':'finite-discrete',
                                                 'domain':['soldered','not-soldered']})
        
        self.location=StateVariable(name=self.name+'-location-state',
                                    domain_dict={'type':'finite-discrete',
                                                 'domain':location_names+['nowhere']})
        
        self.holder=StateVariable(name=self.name+'-holder-state',
                                  domain_dict={'type':'finite-discrete',
                                               'domain':manipulator_names+['nobody']})
                           
class Location(object):
    """A manufacturing location."""
    def __init__(self,name,object_names):
        self.name=name
                
        #Model state variables.         
        self.clean=StateVariable(name=self.name+'-clean',
                                 domain_dict={'type':'finite-discrete',
                                              'domain':['clean','not-clean']})
        
        self.occupying_object=StateVariable(name=self.name+'-occupying-object',
                                            domain_dict={'type':'finite-discrete',
                                                         'domain':object_names+['nothing']})

class Agent(object):
    """A manufacturing agent."""
    def __init__(self,name,ag_type):
        self.name=name

        _agent_types = ['robot_agent','human_agent']
        if ag_type in _agent_types:
            self.type=ag_type
        else:
            raise InvalidTypeError('Agent type must be in '+str(_agent_types))
        
        #Model state variables.        
        self.moving=StateVariable(name=self.name+'-moving-state',
                                  domain_dict={'type':'finite-discrete',
                                               'domain':['moving','not-moving']})

class Manipulator(Agent):
    """Agent capable of performing manipulation."""
    def __init__(self,name,ag_type,object_names):
        super(Manipulator,self).__init__(name,ag_type)

        #Model state variables.    
        self.available=StateVariable(name=self.name+'-availability-state',
                                     domain_dict={'type':'finite-discrete',
                                                  'domain':['available','not-available']})
        
        self.holding=StateVariable(name=self.name+'-holding-state',
                                   domain_dict={'type':'finite-discrete',
                                                'domain':object_names+['nothing']})      

    def pick(self,obj,loc,predicates):
        """
        If the pick action is applicable, returns an episode. Otherwise, returns
        None.
        """        
        preconditions = [(self.available,'available'),(self.moving,'not-moving'),
                         (obj.soldered,'not-soldered'),(self.holding,'nothing'),
                         (obj.location,loc.name),(obj.holder,'nobody'),
                         (loc.occupying_object,obj.name)]

        if check_preconditions(preconditions,predicates):                    
            start_effects={self.available:'not-available',
                           self.moving:'moving'}

            end_effects={self.available:'available',
                         self.moving:'not-moving',
                         self.holding:obj.name,
                         obj.location:'nowhere',
                         obj.holder:self.name,
                         loc.occupying_object:'nothing'}
            
            return Episode(duration={'ctype':'controllable','lb':20,'ub':100},
                           action='(pick '+self.name+' '+obj.name+' '+loc.name+')',
                           start_effects=start_effects,end_effects=end_effects)

        else: #Not applicable
            return None

    def place(self,obj,loc,predicates):
        """
        If the place action is applicable, returns an episode. Otherwise, returns
        None.
        """
        preconditions = [(self.available,'available'),(self.moving,'not-moving'),
                         (self.holding,obj.name),(obj.location,'nowhere'),
                         (obj.holder,self.name),(loc.occupying_object,'nothing')]        

        if check_preconditions(preconditions,predicates):                    
            start_effects={self.available:'not-available',
                           self.moving:'moving'}

            end_effects={self.available:'available',
                         self.moving:'not-moving',
                         self.holding:'nothing',
                         obj.location:loc.name,
                         obj.holder:'nobody',
                         loc.occupying_object:obj.name}

            return Episode(duration={'ctype':'controllable','lb':20,'ub':100},
                           action='(place '+self.name+' '+obj.name+' '+loc.name+')',
                           start_effects=start_effects,end_effects=end_effects)

        else: #Not applicable
            return None

    def clean(self,obj,loc,predicates):
        """
        If the clean action is applicable, returns an episode. Otherwise, returns
        None.
        """
        if not obj.type=='cleanertype':
            return None

        preconditions = [(self.available,'available'),(self.moving,'not-moving'),
                         (self.holding,obj.name),(obj.holder,self.name),
                         (loc.occupying_object,'nothing')]

        if check_preconditions(preconditions,predicates):                    
            start_effects={self.available:'not-available',
                           self.moving:'moving',
                           loc.occupying_object:obj.name}

            end_effects={self.available:'available',
                         self.moving:'not-moving',
                         loc.occupying_object:'nothing',
                         loc.clean:'clean'}

            return Episode(duration={'ctype':'controllable','lb':10,'ub':100},
                           action='(clean '+self.name+' '+obj.name+' '+loc.name+')',
                           start_effects=start_effects,end_effects=end_effects)

        else: #Not applicable
            return None

    def solder(self,obj,solder,loc,predicates):
        """
        If the solder action is applicable, returns an episode. Otherwise, returns
        None. There is a bug in the boeing.rmpl program.
        """
        if not (self.type=='human_agent' and solder.type=='soldertype' and obj.type=='componenttype'):
            return None

        preconditions = [(self.available,'available'),(self.moving,'not-moving'),
                         (self.holding,solder.name),(obj.holder,'nobody'),
                         (obj.soldered,'not-soldered'),(solder.holder,self.name),
                         (obj.location,loc.name),(loc.clean,'clean'),
                         (solder.location,'nowhere')]

        if check_preconditions(preconditions,predicates):                    
            start_effects={self.available:'not-available',
                           self.moving:'moving'}

            end_effects={self.available:'available',
                         self.moving:'not-moving',
                         obj.soldered:'soldered',
                         loc.clean:'not-clean'}

            return Episode(duration={'ctype':'controllable','lb':15,'ub':100},
                           action='(solder '+self.name+' '+obj.name+' '+loc.name+')',
                           start_effects=start_effects,end_effects=end_effects)

        else: #Not applicable
            return None      
              
def check_preconditions(assignment_tuples,predicates):
    """
    Checks if a list of preconditions in the form of a conjunction of predicates
    is satisfied or not.
    """
    for (svar,val) in assignment_tuples:
        if (not svar in predicates) or (predicates[svar]!=val):
            return False
    return True     
     

       



   