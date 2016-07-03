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

Module defining episodes and how the can be composed according to the 'episode algebra'.

@author: Pedro Santana (psantana@mit.edu).
"""
from .defs import ConditionalElement,ChoiceAssignment,Event
from .utils import valid_assignment
from .constraints import TemporalConstraint
from .rmpylexceptions import InvalidTypeError,CompositionError

class Episode(ConditionalElement):
    """
    Class representing an episode.
    """
    def __init__(self,start=None,end=None,**kwargs):
        super(Episode,self).__init__(**kwargs)
        self.properties['start'] = Event() if start==None else start #Start event
        self.properties['end'] = Event() if end==None else end #End event

        #Duration specified as dictionary of parameters of a TemporalConstraint
        dur_dict = kwargs['duration'] if 'duration' in kwargs else {'ctype':'controllable','lb':0.0,'ub':float('inf')}
        self.duration = dur_dict

        self.properties['action'] = kwargs['action'] if 'action' in kwargs else ''

        #If no temporal constraints have been specified, creates an empty set
        if not 'temporal_constraints' in kwargs:
            self.properties['temporal_constraints']=set()
        #Otherwise, make sure the temporal constraints are represented as a set
        else:
            self.properties['temporal_constraints'] = set(self.properties['temporal_constraints'])


        #Preconditions and effects
        _conditions_and_effects = [ 'start_conditions','end_conditions',
                                    'start_effects','end_effects']
        for el in _conditions_and_effects:
            self.properties[el] = kwargs[el] if el in kwargs else {}
            if not valid_assignment(self.properties[el]):
                raise InvalidTypeError('Invalid assignments in preconditions or effects.')

        #Extracts state constraints passed as keyword arguments
        _state_constraint_types = [ 'start_state_constraints',
                                    'end_state_constraints',
                                    'during_state_constraints']

        #Initializes the state constraints with empty sets
        for sc_type in _state_constraint_types:
            self.properties[sc_type] = set()

        #Adds state constraints that might have been provided as keyword arguments
        if 'start_state_constraints' in kwargs:
            for sc in kwargs['start_state_constraints']:
                self.add_start_state_constraint(sc)

        if 'end_state_constraints' in kwargs:
            for sc in kwargs['end_state_constraints']:
                self.add_end_state_constraint(sc)

        if 'during_state_constraints' in kwargs:
            for sc in kwargs['during_state_constraints']:
                self.add_during_state_constraint(sc)

        #Overall state constraints are added to start, end, and during fields.
        if 'overall_state_constraints' in kwargs:
            for sc in kwargs['overall_state_constraints']:
                self.add_start_state_constraint(sc)
                self.add_end_state_constraint(sc)
                self.add_during_state_constraint(sc)

    @property
    def start(self):
        """Start event object."""
        return self.properties['start']

    @start.setter
    def start(self,new_start):
        """Sets the start event."""
        self.properties['start'] = new_start
        self.duration.start = new_start

    @property
    def end(self):
        """End event object."""
        return self.properties['end']

    @end.setter
    def end(self,new_end):
        """Sets the end event."""
        self.properties['end'] = new_end
        self.duration.end = new_end

    @property
    def action(self):
        """Action performed in this episode."""
        return self.properties['action']

    @action.setter
    def action(self,new_action):
        """Action performed in this episode."""
        self.properties['action']=new_action

    @property
    def duration(self):
        """Temporal constraint representing the episode's duration."""
        return self.properties['duration']

    @duration.setter
    def duration(self,new_duration_dict):
        """Modifies the temporal constraint representing the duration."""
        if isinstance(new_duration_dict,dict):
            dur = TemporalConstraint(start=self.start,end=self.end,**new_duration_dict)
            #Should the episode have different guards for the start and end events,
            #makes sure the duration is consistent with the guard for the end event
            #(always a subset of the guard of the start event.)
            dur.support = self.properties['end'].copy_support()
            self.properties['duration'] = dur
        else:
            raise InvalidTypeError('A duration dictionary should be provided when setting the duration of an RMPyL Episode.')

    @property
    def start_conditions(self):
        """PDDL-like conditions at the start of the episode."""
        return self.properties['start_conditions']

    @property
    def end_conditions(self):
        """PDDL-like conditions at the end of the episode."""
        return self.properties['end_conditions']

    @property
    def start_effects(self):
        """PDDL-like effects at the start of the episode."""
        return self.properties['start_effects']

    @property
    def end_effects(self):
        """PDDL-like effects at the end of the episode."""
        return self.properties['end_effects']

    @property
    def composition(self):
        """
        Returns the type of composition for composite episodes, or an empty
        string if the episode is primitive.
        """
        if 'parallel' in self.properties: #Composite parallel
            return 'parallel'
        elif 'sequence' in self.properties: #Composite sequence
            return 'sequence'
        elif 'choose' in self.properties: #Composite choice
            return 'choose'
        else:
            return None

    @property
    def internal_episodes(self):
        """
        Internal episodes to the composite episode, or an empty list if the
        episode is primitive.
        """
        comp = self.composition
        return self.properties[comp] if comp != None else []

    @property
    def terminal(self):
        """
        Returns whether an episode is terminal or not. By default, they are not.
        """
        return ('terminal' in self.properties) and (self.properties['terminal'])

    @property
    def temporal_constraints(self):
        """
        Temporal constraints internal to this episode.
        """
        return self.properties['temporal_constraints'] | {self.duration}

    @property
    def all_temporal_constraints(self):
        """
        Recursively extracts all temporal constraints in the episode.
        """
        if self.composition == None: #Primitive episode
            return self.temporal_constraints
        else:
            all_tcs={}
            for internal_epi in self.internal_episodes:
                all_tcs.update(internal_epi.all_temporal_constraints)
            return all_tcs

    @property
    def start_state_constraints(self):
        """
        State constraints that must hold at the start event.
        """
        return self.properties['start_state_constraints']

    @property
    def end_state_constraints(self):
        """
        State constraints that must hold at the end event.
        """
        return self.properties['end_state_constraints']

    @property
    def during_state_constraints(self):
        """
        State constraints that must hold during the execution of an episode.
        """
        return self.properties['during_state_constraints']

    @property
    def overall_state_constraints(self):
        """
        State constraints that should hold at the start, end, and during an episode.
        """
        return self.start_state_constraints.intersection(self.end_state_constraints.intersection(self.during_state_constraints))

    @property
    def state_constraints(self):
        """
        Union of all state constraints for this episode
        """
        return self.start_state_constraints.union(self.end_state_constraints.union(self.during_state_constraints))

    @property
    def all_state_constraints(self):
        """
        Recursively extracts all state constraints in the episode.
        """
        if self.composition == None: #Primitive episode
            return self.state_constraints
        else:
            all_scs={}
            for internal_epi in self.internal_episodes:
                all_scs.update(internal_epi.all_state_constraints)
            return all_scs

    def add_temporal_constraint(self,tc):
        """
        Adds a temporal constraint to the episode.
        """
        self.properties['temporal_constraints'].add(tc)

    def add_start_state_constraint(self,sc):
        """
        Adds a state constraint that must hold at the start of the episode (but
        not necessarily after that).
        """
        self.properties['start_state_constraints'].add(sc)

    def add_end_state_constraint(self,sc):
        """
        Adds a state constraint that must hold at the end of the episode (but
        not necessarily before that).
        """
        self.properties['end_state_constraints'].add(sc)

    def add_during_state_constraint(self,sc):
        """
        Adds a state constraint that must hold during the execution of an episode
        (but not necessarily at the beginning or end).
        """
        self.properties['during_state_constraints'].add(sc)

        #A 'during' state constraints for a composite episode corresponds to
        #an overall state constraints to the inner episodes.
        for ep in self.internal_episodes:
            ep.add_overall_state_constraint(sc)

    def add_overall_state_constraint(self,sc):
        """
        Syntactic sugar to express that a state constraint should hold at the start,
        end, and during an episode.
        """
        self.add_start_state_constraint(sc)
        self.add_end_state_constraint(sc)
        self.add_during_state_constraint(sc)

    def __add__(self,other):
        """
        Addition combines two episodes in parallel.
        """
        return parallel_composition(self,other)

    def __mul__(self,other):
        """
        Multiplication combines two episodes in sequence.
        """
        return sequence_composition(self,other)

    def __repr__(self):
        str_prop = '' if len(self.properties)==0 else str(self.properties)
        return 'Episode(at 0x%x) '%(id(self))+str_prop


def sequence_composition(*episodes,**kwargs):
    """
    Creates a sequential composition of episodes.
    """
    return _optimized_sequence_composition(*episodes,**kwargs)
    #return _stable_sequence_composition_with_extra_events(*episodes,**kwargs)


def _optimized_sequence_composition(*episodes,**kwargs):
    """
    Optimized version of the sequence composition that reuses the start and end
    events of the start and end episodes, respectively. Should be considered
    experimental.
    """
    if 'start' in kwargs:
        seq_start = kwargs['start']
        del kwargs['start']
    else:
        seq_start = episodes[0].start

    if 'end' in kwargs:
        seq_end = kwargs['end']
        del kwargs['end']
    else:
        seq_end = episodes[-1].end

    composition_tcs=[] #Extra temporal constraints

    #If no_wait=True was provided as a keyword argument, introduces a controllable
    #[0,0] between every episode in the sequential composition, i.e., one episode
    #should be executed immediately after the other. Otherwise, there is a controllable
    #wait.
    tc_ub = 0.0 if 'no_wait' in kwargs and kwargs['no_wait'] else float('inf')

    for i in range(len(episodes)-1):
        if episodes[i].terminal:
            raise CompositionError('Cannot execute terminal episode in sequence with others.')

        #Propagates the support from left to right
        #episodes[i+1]._propagate_support_recursive(episodes[i].end.support)
        propagate_support_recursive(episodes[i+1],episodes[i].end.support)

        #Sequence composition constraint.
        tc = TemporalConstraint(start=episodes[i].end,end=episodes[i+1].start,
                                ctype='controllable',lb=0.0,ub=tc_ub)

        tc.support = episodes[i].end.copy_support()
        composition_tcs.append(tc)

    ep = Episode(start=seq_start,end=seq_end,sequence=episodes,
                 temporal_constraints=composition_tcs,**kwargs)
    return ep


def _stable_sequence_composition_with_extra_events(*episodes,**kwargs):
    """
    Stable version of the sequence composition, which creates extra events at the
    start and end of a sequence.
    """
    if 'start' in kwargs:
        seq_start = kwargs['start']
        del kwargs['start']
    else:
        seq_start = Event()

    if 'end' in kwargs:
        seq_end = kwargs['end']
        del kwargs['end']
    else:
        seq_end = Event()

    composition_tcs=[] #Extra temporal constraints

    #If no_wait=True was provided as a keyword argument, introduces a controllable
    #[0,0] between every episode in the sequential composition, i.e., one episode
    #should be executed immediately after the other. Otherwise, there is a controllable
    #wait.
    tc_ub = 0.0 if 'no_wait' in kwargs and kwargs['no_wait'] else float('inf')

    #Precedence constraint for sequence start
    composition_tcs.append(TemporalConstraint(start=seq_start,
                                              end=episodes[0].start,
                                              ctype='controllable',lb=0.0,ub=tc_ub))

    for i in range(len(episodes)-1):
        if episodes[i].terminal:
            raise CompositionError('Cannot execute terminal episode in sequence with others.')

        #Propagates the support from left to right
        #episodes[i+1]._propagate_support_recursive(episodes[i].end.support)
        propagate_support_recursive(episodes[i+1],episodes[i].end.support)

        #Sequence composition constraint.
        tc = TemporalConstraint(start=episodes[i].end,end=episodes[i+1].start,
                                ctype='controllable',lb=0.0,ub=tc_ub)

        tc.support = episodes[i].end.copy_support()
        composition_tcs.append(tc)

    #End event of a sequence has the same support as the end event of the last
    #episode
    seq_end.support = episodes[-1].end.copy_support()

    #Precedence constraint for sequence end
    tc = TemporalConstraint(start=episodes[-1].end,end=seq_end,
                            ctype='controllable',lb=0.0,ub=tc_ub)
    tc.support = seq_end.copy_support()
    composition_tcs.append(tc)

    ep = Episode(start=seq_start,end=seq_end,sequence=episodes,
                 temporal_constraints=composition_tcs,**kwargs)
    return ep


def parallel_composition(*episodes,**kwargs):
    """
    Creates a parallel composition of episodes.
    """
    for ep in episodes:
        if ep.terminal:
            raise CompositionError('Cannot execute terminal episode in parallel with others.')

    if 'start' in kwargs:
        par_start = kwargs['start']
        del kwargs['start']
    else:
        par_start = Event()

    if 'end' in kwargs:
        par_end = kwargs['end']
        del kwargs['end']
    else:
        par_end = Event()

    #par_start = kwargs['start'] if 'start' in kwargs else Event()
    #par_end = kwargs['end'] if 'end' in kwargs else Event()
    #par_start = Event(); par_end = Event()

    composition_tcs_start=[]; composition_tcs_end=[] #Extra temporal constraints
    for ep in episodes:
        tc_start = TemporalConstraint(start=par_start,end=ep.start,
                                      ctype='controllable',lb=0.0,ub=float('inf'))
        composition_tcs_start.append(tc_start)

        tc_end = TemporalConstraint(start=ep.end,end=par_end,
                                    ctype='controllable',lb=0.0,ub=float('inf'))
        par_end.support_AND(ep.end.copy_support())
        composition_tcs_end.append(tc_end)

    #The temporal constraints for the end event should have the same guard as
    #the end event, since it is the intersection of all the guards of the
    #episodes being executed in parallel.
    for tc in composition_tcs_end:
        tc.support = par_end.copy_support()

    ep = Episode(start=par_start,end=par_end,parallel=episodes,
                 temporal_constraints=composition_tcs_start+composition_tcs_end,**kwargs)
    return ep


def choose_composition(choice,*episodes,**kwargs):
    """
    Creates a disjunction of episodes due to a choice event (controllable or not).
    """
    if 'end' in kwargs: #Event where choices converge
        choice_end = kwargs['end']
        del kwargs['end']
    else:
        choice_end = Event()

    #choice_end = kwargs['end'] if 'end' in kwargs else Event()
    #choice_end = Event()

    composition_tcs=[] #Extra temporal constraints

    terminal_episodes = [ep for ep in episodes if ep.terminal]
    guard_negations=[]
    for i,ep in enumerate(episodes):
        #Choice assignment that activates the episode
        assignment = ChoiceAssignment(choice,choice.domain[i],negated=False)

        #Propagates the assignment forward, in the case of composite episodes
        #ep._propagate_support_recursive([[assignment]])
        propagate_support_recursive(ep,[[assignment]])

        #Adds a precedence temporal constraints between the choice and the
        #start of the episode
        tc_start = TemporalConstraint(start=choice,end=ep.start,
                                      ctype='controllable',lb=0.0,ub=float('inf'))
        tc_start.add_support_assignment(assignment)
        composition_tcs.append(tc_start)

        #If the episode isn't terminal, adds the temporal constraints at the
        #end as well.
        if not ep in terminal_episodes:
            tc_end = TemporalConstraint(start=ep.end,end=choice_end,
                                        ctype='controllable',lb=0.0,ub=float('inf'))
            tc_end.add_support_assignment(assignment)
            composition_tcs.append(tc_end)
        else:
            guard_negations.append(ChoiceAssignment(choice,choice.domain[i],negated=True))

    #Terminal episodes, in which case we need to modify the support of the end event
    #because not all branches from the choice converge.
    terminal=False
    if len(terminal_episodes)!=0: #There are terminal episodes
        if(len(guard_negations)==len(choice.domain)): #All episodes are terminal
            terminal=True
        else: #Updates the label of the end event, if only a subset of episodes are terminal
            choice_end.set_conjunction(guard_negations)

    ep = Episode(start=choice,end=choice_end,choose=episodes,choice=choice,
                 terminal=terminal,temporal_constraints=composition_tcs,**kwargs)
    return ep


def propagate_support_recursive(episode,other_support):
    """
    Propagates another support through an episode by performing a Cartesian
    product between the other support, and the support of each constituent of
    the episode.
    """
    #Ensures that the episode, its start and end events, along with the duration
    #constraint, all have consistent supports.
    episode.support_AND(other_support)
    episode.start.support_AND(other_support)
    episode.end.support_AND(other_support)
    episode.duration.support_AND(other_support)

    #If this is a composite episode, propagates the other support to the
    #component episodes as well.
    if episode.composition != None:
        for tc in episode.temporal_constraints:
            tc.support_AND(other_support)

        for ep in episode.internal_episodes:
            propagate_support_recursive(ep,other_support)
