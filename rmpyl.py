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

This module defines the RMPyL class, which represents RMPL programs.

@author: Pedro Santana (psantana@mit.edu).
"""
from .defs import NamedElement,Choice
from .utils import valid_assignment
from .constraints import TemporalConstraint
from .episodes import Episode,sequence_composition,parallel_composition,choose_composition
from .rmpylexceptions import InvalidTypeError,IDError,CompositionError,DuplicateElementError
from .ptpn import to_ptpn

class RMPyL(NamedElement):
    """
    Class representing an RMPL program.
    """
    def __init__(self,**kwargs):
        super(RMPyL,self).__init__(**kwargs)

        #Default RMPyL program names, in case one hasn't been specified.
        if not 'name' in kwargs:
            self.name = 'run()'

        self._plan_episode= None     #Composite episode representing the plan
        self._initial_state = {}
        self._goal_state = {}
        self._user_chance_constraints=set()
        self._user_temporal_constraints=set()
        self._user_state_constraints=set()
        self._episode_temporal_constraints=set()
        self._primitive_episodes=set()
        self._events = set()
        self._user_state_variables = set()
        self._cached=False
        self._episode_mapping={}
        #self._event_successors={}

    @property
    def plan(self):
        """Returns a reference to the plan episode."""
        return self._plan_episode

    @plan.setter
    def plan(self,new_plan):
        """Sets a new value for the plan episode."""
        if not isinstance(new_plan,Episode):
            raise InvalidTypeError('Plans should be represented as Episodes.')
        self._plan_episode = new_plan
        self._cached=False

    @property
    def first_event(self):
        """
        First event in the program.
        """
        #self._update_recursive()
        return self._plan_episode.start if self._plan_episode!= None else None

    @property
    def last_event(self):
        """
        Last event in the program.
        """
        #self._update_recursive()
        return self._plan_episode.end if self._plan_episode!= None else None

    @property
    def initial_state(self):
        """
        State of the system at the first event.
        """
        return self._initial_state

    @initial_state.setter
    def initial_state(self,new_initial_state):
        """
        Sets a new initial state at the first event.
        """
        if valid_assignment(new_initial_state):
            self._initial_state = new_initial_state
        else:
            raise InvalidTypeError('Invalid form for initial state.')

    @property
    def goal_state(self):
        """
        State of the system at the last event.
        """
        return self._goal_state

    @goal_state.setter
    def goal_state(self,new_goal_state):
        """
        Sets a new goal state at the last event.
        """
        if valid_assignment(new_goal_state):
            self._goal_state = new_goal_state
            # scope=[];values=[]
            # for svar,val in goal_state.items():
            #     scope.append(svar); values.append(val)
            # goal_sc = AssignmentStateConstraint(scope=scope,values=values)
            # self.plan.add_end_state_constraint(goal_sc)
        else:
            raise InvalidTypeError('Invalid form for goal state.')

    @property
    def episodes(self):
        """
        List of all episodes (primitive and composite) in the program
        """
        return list(self.episode_mapping.values())

    @property
    def primitive_episodes(self):
        """
        List of primitive episodes in the plan (as opposed to composite).
        """
        self._update_recursive()
        return self._primitive_episodes

    @property
    def events(self):
        """List of events."""
        self._update_recursive()
        return self._events

    @property
    def choices(self):
        """List of choice events."""
        return [e for e in self.events if isinstance(e,Choice)]

    @property
    def decisions(self):
        """List of decisions in the program."""
        return [c for c in self.choices if c.type=='controllable']

    @property
    def observations(self):
        """List of observations in the program."""
        return [c for c in self.choices if c.type in ['uncontrollable','probabilistic']]

    @property
    def state_variables(self):
        """Set of state variables."""
        self._state_variables = set()
        for sc in self.state_constraints: #All variables in state constraints
            for svar in sc.scope:
                self._state_variables.add(svar)
        for svar in self.initial_state.keys(): #All variables in the initial state
            self._state_variables.add(svar)
        #Union with all user-defined variables.
        return self._state_variables.union(self._user_state_variables)

    @property
    def chance_constraints(self):
        """
        List of chance constraints.
        """
        #self._update_all_user_constraint_guards()
        return self._user_chance_constraints

    @property
    def state_constraints(self):
        """
        List of state constraints.
        """
        self._update_recursive()
        return self._user_state_constraints

    @property
    def user_defined_temporal_constraints(self):
        """
        Temporal constraints externally-imposed by the program.
        """
        self._update_all_user_constraint_guards()
        return self._user_temporal_constraints

    @property
    def internal_episode_temporal_constraints(self):
        """
        Temporal constraints internally-created in episodes
        """
        self._update_recursive()
        return self._episode_temporal_constraints

    @property
    def temporal_constraints(self):
        """
        List of temporal constraints.
        """
        return self.user_defined_temporal_constraints.union(self.internal_episode_temporal_constraints)

    @property
    def episode_mapping(self):
        """
        Mapping from element IDs to element objects.
        """
        self._update_recursive()
        return self._episode_mapping

    # @property
    # def event_successors(self):
    #     """
    #     Dictionary mapping events to a list of their successors.
    #     """
    #     self._update_recursive()
    #     return self._event_successors

    def episode_by_id(self,ep_id):
        """
        Retrieves an episode by its ID.
        """
        if ep_id in self.episode_mapping:
            return self.episode_mapping[ep_id]
        else:
            raise IDError('No episode corresponding to ID '+str(ep_id))

    def _add_episode_mapping(self,episode):
        """
        Adds an episode to the episode mapping dictionary.
        """
        if episode.id in self._episode_mapping:
            if self._episode_mapping[episode.id]!=episode:
                raise IDError('Object ID redefinition.')
        else:
            self._episode_mapping[episode.id]=episode

    # def _update_event_successors(self,episode):
    #     """
    #     Updates the event succession relationship.
    #     """
    #     composition = episode.composition #Type of episode composition
    #
    #     if composition==None: #Episode is primitive
    #         #Succession is just start->end
    #         self._event_successors[episode.start]=[episode.end]
    #
    #     elif composition=='sequence':#Episode is a sequence of others
    #         #Succession is a chain
    #         ep_sequence = episode.internal_episodes
    #
    #         #The start of the sequence precedes the first episode
    #         self._event_successors[episode.start]=[ep_sequence[0].start]
    #         for i in range(len(ep_sequence)-1):
    #             self._event_successors[ep_sequence[i].end]=[ep_sequence[i+1].start]
    #         #The end of the sequence succeeds the last episode
    #         self._event_successors[ep_sequence[-1].end]=[episode.end]
    #
    #     elif composition=='parallel'or composition=='choose': #Parallel or choice composition
    #         internal_starts = [e.start for e in episode.internal_episodes]
    #         self._event_successors[episode.start] = internal_starts
    #
    #         for e_end in [e.end for e in episode.internal_episodes]:
    #             self._event_successors[e_end] = [episode.end]
    #     else:
    #         raise InvalidTypeError('Invalid type of episode composition: '+composition)

    def sequence(self,*episodes_or_progs,**kwargs):
        """
        Adds a sequential composition of episodes to the plan.
        """
        episodes = self._extract_episodes_and_constraints(episodes_or_progs)
        ep_seq = sequence_composition(*episodes,**kwargs)
        self._add_episode_mapping(ep_seq)
        return ep_seq

    def parallel(self,*episodes_or_progs,**kwargs):
        """
        Adds a parallel composition of episodes to the plan.
        """
        episodes = self._extract_episodes_and_constraints(episodes_or_progs)
        ep_par = parallel_composition(*episodes,**kwargs)
        self._add_episode_mapping(ep_par)
        return ep_par

    def choose(self,choice,*episodes_or_progs,**kwargs):
        """
        Adds a disjunction of episodes represented by a choice node.
        """
        if not isinstance(choice,Choice):
            raise InvalidTypeError('choice argument should be of type Choice.')

        episodes = self._extract_episodes_and_constraints(episodes_or_progs)

        if len(choice.domain)!=len(episodes):
            raise CompositionError('Number of episodes must match the size of the choice\'s domain.')

        ep_choice = choose_composition(choice,*episodes,**kwargs)
        self._add_episode_mapping(ep_choice)
        return ep_choice

    def decide(self,choice_dict,*episodes_or_progs,**kwargs):
        """
        Adds a controllable decision variable to the plan. Syntactic sugar on
        top of choose.
        """
        if 'ctype' in choice_dict:
            raise InvalidTypeError('Decisions are necessarily controllable, so not type is necessary.')
        choice = Choice(ctype='controllable',**choice_dict)
        return self.choose(choice,*episodes_or_progs,**kwargs)

    def observe(self,choice_dict,*episodes_or_progs,**kwargs):
        """
        Adds a uncontrollable decision variable to the plan. Syntactic sugar on
        top of choose.
        """
        if (not 'ctype' in choice_dict) or (not choice_dict['ctype'] in ['uncontrollable','probabilistic']):
            raise InvalidTypeError('Observations must be uncontrollable or probabilistic.')
        choice = Choice(**choice_dict)
        return self.choose(choice,*episodes_or_progs,**kwargs)

    def loop(self,episode_func,repetitions,run_utility,stop_utility,*episode_func_args,**kwargs):
        """
        Creates a simple loop structure representing the choice of executing the
        actions defined by episode_func one or more times.
        """
        if repetitions==1:
            return self.decide({'name':'loop-choice-'+str(repetitions),
                                'domain':['RUN','STOP'],
                                'utility':[run_utility,stop_utility]},
                                episode_func(*episode_func_args),
                                Episode())
        else:
            return self.decide({'name':'loop-choice-'+str(repetitions),
                                'domain':['RUN','STOP'],
                                'utility':[run_utility,stop_utility]},
                                self.sequence(episode_func(*episode_func_args),
                                              self.loop(episode_func,repetitions-1,
                                                               run_utility,stop_utility,
                                                               *episode_func_args)),
                                Episode())

    def add_temporal_constraint(self,tc):
        """
        Adds a temporal constraint to the plan.
        """
        if not tc in self._user_temporal_constraints:
            self._user_temporal_constraints.add(tc)
            self._update_temporal_constraint_guard(tc)
            self._cached=False
        else:
            raise DuplicateElementError('Tried adding repeated temporal constraint '+str(tc))

    def remove_temporal_constraint(self,tc):
        """
        Removes a temporal constraint from the internal sets.
        """
        self._user_temporal_constraints.discard(tc)
        for ep in self.episodes:
            tcs = ep.temporal_constraints
            if tc in tcs:
                ep.temporal_constraints.remove(tc)
            if tc == ep.duration:
                ep.duration = {'ctype':'controllable','lb':0.0,'ub':float('inf')}

        self._cached=False

    def simplify_temporal_constraints(self):
        """
        Detects when two controllable temporal constraints are placed over the
        same pair of events, and simplies them.
        """
        remove_set=set()
        tc_list = list(self.temporal_constraints)
        for tc_index,tc1 in enumerate(tc_list):
            if not tc1 in remove_set:
                if tc1.start.id == tc1.end.id or tc1.start.name == tc1.end.name :
                    if tc1.type != 'controllable' or tc1.lb!=0.0:
                        raise InvalidTypeError('Adding an invalid temporal constraint between an event and itself')
                    else:
                        remove_set.add(tc1)
                else:
                    for tc2 in tc_list[tc_index+1:]:
                        if tc1.constraint_same_events(tc2) and tc1.type=='controllable':
                            tc1.bounds = (max(tc1.lb,tc2.lb),min(tc1.ub,tc2.ub))
                            remove_set.add(tc2)

        for tc in remove_set:
            self.remove_temporal_constraint(tc)


    def add_chance_constraint(self,cc):
        """
        Adds a chance constraint to the plan.
        """
        if not cc in self._user_chance_constraints:
            self._user_chance_constraints.add(cc)
            #self._update_all_user_constraint_guards()
            self._cached=False
        else:
            raise DuplicateElementError('Tried adding repeated chance constraint '+str(cc))

    # def add_state_constraint(self,sc):
    #     """
    #     Adds a state constraint to the plan.
    #     """
    #     if not sc in self._user_state_constraints:
    #         self._user_state_constraints.add(cc)
    #         self._update_all_user_constraint_guards()
    #     else:
    #         raise DuplicateElementError('Tried adding repeated state constraint '+str(sc))

    def add_state_variable(self,sv):
        """
        Adds a new state variable to the program
        """
        self._user_state_variables.add(sv)
        self._cached=False

    def add_overall_state_constraint(self,state_constraint):
        """
        Syntactic sugar for imposing a state constraint on the whole program.
        """
        self.plan.add_overall_state_constraint(state_constraint)
        self._cached=False

    def add_overall_temporal_constraint(self,**kwargs):
        """
        Syntactic sugar for imposing a temporal constraints on the total duration
        of the plan, which is a very common thing in RMPL programs. Returns the
        user-defined temporal constraint.
        """
        overall = TemporalConstraint(start=self.first_event,end=self.last_event,
                                     **kwargs)
        self.add_temporal_constraint(overall)
        return overall

    def to_ptpn(self,filename,exclude_op=['__stop__']):
        """
        Exports the RMPyL program to a pTPN XML.
        """
        return to_ptpn(prog=self,filename=filename,exclude_op=exclude_op)

    def __add__(self,other):
        """
        Parallel combination of the current plan with another episode. Does not
        modify the plan.
        """
        if isinstance(other,Episode):
            return other if self.plan==None else self.plan+other
        elif isinstance(other,RMPyL):
            return other.plan if self.plan==None else self.plan+other.plan
        else:
            raise InvalidTypeError('RMPyL programs can only be added with other programs or episodes.')

    def __iadd__(self,other):
        """
        Parallel combination of the current plan with another episode. Modifies
        and returns the plan.
        """
        ep_iseq = self.__add__(other)
        self._add_episode_mapping(ep_iseq)
        self.plan = ep_iseq
        return self

    def __mul__(self,other):
        """
        Sequential combination of the current plan with another episode. Does not
        modify the plan.
        """
        if isinstance(other,Episode):
            return other if self.plan==None else self.plan*other
        elif isinstance(other,RMPyL):
            return other.plan if self.plan==None else self.plan*other.plan
        else:
            raise InvalidTypeError('RMPyL programs can only be multiplied with other programs or episodes.')

    def __imul__(self,other):
        """
        Sequential combination of the current plan with another episode.
        """
        ep_ipar = self.__mul__(other)
        self._add_episode_mapping(ep_ipar)
        self.plan = ep_ipar
        return self

    def _extract_episodes_and_constraints(self,episodes_or_progs):
        """
        Extracts episodes and user-defined constraints from a list of pure
        episodes or RMPyL programs.
        """
        episodes=[]; user_tcs=set()
        for el in episodes_or_progs:
            if isinstance(el,RMPyL):
                episodes.append(el.plan)
                user_tcs.update(el.user_defined_temporal_constraints)
            elif isinstance(el,Episode):
                episodes.append(el)
            else:
                raise InvalidTypeError('Element must be Episode or RMPyL program.')

        for tc in user_tcs:
            self.add_temporal_constraint(tc)

        return episodes #Only returns episodes

    def _update_recursive(self,force=False):
        """Recursively computes primitive episodes, temporal constraints, and
        temporal events, caching the results at the end."""
        if (force or (not self._cached)):
            #Quantities do not have to be recomputed if the plan does not change
            self._cached=True

            if self._plan_episode!=None:
                episodes,temp_consts,state_consts,events = self._recursive_traversal([self._plan_episode])
            else:
                episodes,temp_consts,state_consts,events=[],[],[],[]

            self._primitive_episodes=set(episodes)
            if len(self._primitive_episodes)!=len(episodes):
                raise DuplicateElementError('Found repeated primitive episode.')

            self._episode_temporal_constraints=set(temp_consts)
            if len(self._episode_temporal_constraints)!=len(temp_consts):
                raise DuplicateElementError('Found repeated internal temporal constraints.')

            #User defined state constraints
            self._user_state_constraints = state_consts

            #Events can appear more than once because of sequential
            #compositions, so we need to keep only the unique set of events. Also,
            #there could be events that only show up in the specification of
            #user-defined temporal constraints, but not episodes.
            user_defined_events=set()
            for user_tc in self._user_temporal_constraints:
                user_defined_events.add(user_tc.start)
                user_defined_events.add(user_tc.end)
            self._events = set(events).union(user_defined_events)

            #Updates the support of user-defined constraints
            self._update_all_user_constraint_guards()

    def _update_all_user_constraint_guards(self):
        """
        Updates the guard conditions of user-specified constraints.
        """
        #I need to catch the exception of inconsistent supports.
        for tc in self._user_temporal_constraints:
            self._update_temporal_constraint_guard(tc)

    def _update_temporal_constraint_guard(self,tc):
        """
        Updates the guard for a single temporal constraint, based on the
        supports for the start and end events.
        """
        tc.clear_support()
        tc.support_AND(tc.start.support)
        tc.support_AND(tc.end.support)

    def _recursive_traversal(self,episodes):
        """
        Recursive function that returns a list of primitive episodes, temporal
        constraints and events.
        """
        if len(episodes)==1:
            ep = episodes[0]
            self._add_episode_mapping(ep)#Updates episode mapping
            # self._update_event_successors(ep)#Updates event successors

            #Temporal constraints from the composition of episodes, if any
            tcs = list(ep.temporal_constraints)

            #FIXME: the duration should not be part of the composition_tcs in
            #the first place (example 16).
            if not ep.duration in tcs:
                #Adds the temporal constraint representing the episode's duration
                tcs.append(ep.duration)

            #State constraints for this episode
            scs = ep.state_constraints

            #Events for this episode
            ep_events=[ep.start,ep.end]

            if ep.composition != None: #Composite episode
                prim_epi,temp_cons,state_cons,rec_events = self._recursive_traversal(ep.internal_episodes)
                return prim_epi,tcs+temp_cons,scs.union(state_cons),ep_events+rec_events
            else: #Primitive episode
                return episodes,tcs,scs,ep_events
        else:
            prim_epi_l,temp_cons_l,state_cons_l,events_l = self._recursive_traversal(episodes[0:1])
            prim_epi_r,temp_cons_r,state_cons_r,events_r = self._recursive_traversal(episodes[1:])

            return prim_epi_l+prim_epi_r,temp_cons_l+temp_cons_r,state_cons_l.union(state_cons_r),events_l+events_r
