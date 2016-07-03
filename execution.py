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

Functions and classes useful for executing RMPyL programs.

@author: Pedro Santana (psantana@mit.edu).
"""
import random

class RMPyLObservationSampler(object):
    """
    Observation generator for an RMPyL program with uncontrollable choices.
    """
    def __init__(self,rmpyl_prog):
        #Observations that are present in the program
        self.observations=rmpyl_prog.observations

    def sample_observations(self):
        """
        Generates the probability distributions for the different observations,
        so that they can be simulated.
        """
        sample_dict={}
        for obs in self.observations:
            domain = obs.properties['domain']
            #If probabilistic, sample from the true distribution
            if obs.type=='probabilistic':
                probabilities = obs.properties['probability']
            #If uncontrollable, sample uniformly from the domain
            else:
                probabilities = [1.0/len(domain)]*len(domain)

            #Samples a value from the discrete probability distribution
            u_sample =random.random()
            acc_prob=0.0
            for val,prob in zip(domain,probabilities):
                acc_prob+=prob
                if u_sample<= acc_prob:
                    sample_dict[obs]=val
                    break

        return sample_dict


# Let's not focus on the problem of deciding the temporal precedence of choices
# in a TPN, since that requires reasoning about the temporal constraints
# themselves.

# Instead, we will only care about choices that can and cannot co-occur. In this
# sense, it is sufficient to just look at their supports. Choices with the exact
# same support will co-occur, whether they are in parallel or in sequence (the
# type of composition only affects their scheduling constraints, not their activation).
# Choices with different supports can be one of two things: either they are in disjoint
# branches, in which case they will never co-occur; or they are hierarchically composed.

class RMPyLTraverser(object):
    """
    Class that allows you to traverse an RMPyL program by providing you with a
    choice hierarchy and constraint activation functions.
    """
    def __init__(self,prog):
        self.prog = prog
        self.choices = list(prog.choices)
        self.temporal_constraints = prog.temporal_constraints

        #choice_activation_dict is a dictionary that maps choices variables to
        #a dictionary of assignments, which in turn leads to the sets of choices
        #that are made active by that choice assignment.
        self.choice_activation_dict,self.initially_active_choices = self._choice_activation()

    def active_temporal_constraints(self,assignments):
        """
        Returns the set of active temporal constraints for a given assignment
        to choice variables.
        """
        return [t for t in self.temporal_constraints if t.is_active(assignments)]

    def _choice_activation(self):
        """
        Internal function that builds the choice activation mapping and determines
        the initial set of active choices in a program.
        """
        support_clusters = group_elements_by_support(self.choices)
        choice_hierarchy={}; initially_active_choices=[]
        if len(support_clusters)>0: #There are choices in the RMPyL program
            initially_active_choices=support_clusters[0]
            for choice_cluster in support_clusters[1:]:
                cluster_support = choice_cluster[0].support
                for c in self.choices:
                    if (not c in choice_cluster):
                        activates,assig = self._activates(c,cluster_support)
                        if activates:
                            if c in choice_hierarchy:
                                choice_hierarchy[c][(assig.value,assig.negated)]=choice_cluster
                            else:
                                choice_hierarchy[c]={(assig.value,assig.negated):choice_cluster}

        return choice_hierarchy,initially_active_choices

    def _activates(self,choice,support):
        """
        Whether a choice activates a support or not.
        """
        for conj_choice in choice.support:
            for conj_support in support:
                if conj_choice < conj_support:
                    diff = conj_support-conj_choice
                    if len(diff)==1:
                        assig = list(diff)[0]
                        if assig.var == choice:
                            return True,assig
        return False,None

def group_elements_by_support(elements):
    """
    Groups conditional elements (those with activating supports) that share the
    same support, i.e., those that must be part of the same execution.
    """
    element_list = elements if isinstance(elements,(list,tuple)) else list(elements)
    index_list = range(len(element_list))
    support_clusters=[]
    while len(index_list)>0:
        #Each support cluster starts with the current first variable
        support_clusters.append([element_list[index_list[0]]])
        remove_index = set([index_list[0]])
        for i in index_list[1:]:
            #If two variables share the same support, removes it from future consideration
            if element_list[index_list[0]].support == element_list[i].support:
                support_clusters[-1].append(element_list[i])
                remove_index.add(i)
        index_list = [i for i in index_list if not i in remove_index]

    #Sorts the supports by their length
    support_clusters.sort(key=lambda clus: sum([len(conj) for conj in clus[0].support]))

    return support_clusters
