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

Module that allows RMPyL programs to be exported to TPN's (or pTPN's).

@author: Pedro Santana (psantana@mit.edu).
"""
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom
from .constraints import AssignmentStateConstraint,LinearStateConstraint

def to_ptpn(prog,filename,exclude_op=[]):
    """
    Converts an RMPyL program into a pretty XML representation. The current
    implementation is ridiculous (prog->XMLTREE->XMLString->XMLDOM->PrettyXMLString),
    but works well.
    """
    #Primitive episode durations
    durations = [ep.duration for ep in prog.primitive_episodes]

    #Temporal constraints that are not durations, so that they don't get added
    #twice in the pTPN
    temporal_constraints = [tc for tc in prog.temporal_constraints if not tc in durations]

    #Removes opearators from the policy, leaving only their temporal duration
    episode_list=[]
    for e in prog.primitive_episodes:
        if e.action in exclude_op:
            temporal_constraints.append(e.duration)
        else:
            episode_list.append(e)

    root = ET.Element('tpns') #pTPN root
    root.set('xmlns','http://mers.csail.mit.edu/tpn')
    tpn_xml = ET.SubElement(root,'tpn')

    #HACK to make a list of temporal constraints be recognized as a valid TPN
    for bogus_event in prog.events:
        break
    export_header_fields(tpn_xml,prog,bogusID=bogus_event.id) #Header fields

    #Adding all temporal events,including choices
    xml_events = ET.SubElement(tpn_xml,'events')
    for ev in prog.events:
        xml_events.append(export_temporal_event(ev))

    #Adding temporal constraints
    xml_tcs = ET.SubElement(tpn_xml,'temporal-constraints')
    for tc in temporal_constraints:
        xml_tcs.append(export_temporal_constraint(tc))

    #Adding primitive episodes
    xml_episodes = ET.SubElement(tpn_xml,'episodes')
    for ep in episode_list:
        xml_episodes.append(export_episode(ep))

    #Adding chance constraints
    xml_ccs = ET.SubElement(tpn_xml,'chance-constraints')
    for cc in prog.chance_constraints:
        xml_ccs.append(export_chance_constraint(cc))

    #Adding decision variables
    xml_decisions = ET.SubElement(tpn_xml,'decision-variables')
    for c in prog.choices:
        xml_decisions.append(export_choice(c))

    #Adding state variables
    xml_state_variables = ET.SubElement(tpn_xml,'state-variables')
    for sv in prog.state_variables:
        xml_state_variables.append(export_state_variable(sv))

    #Adding initial state
    tpn_xml.append(export_state(prog.initial_state,initial=True))

    #Converts XML tree object to string
    tree_str = ET.tostring(root, 'utf-8')

    #Writes a pretty XML to a file.
    if filename!=None:
        reparsed = minidom.parseString(tree_str)
        with open(filename,'w') as fi:
            fi.write(reparsed.toprettyxml(indent="\t"))

    return tree_str #Returns TPN as a string


def export_header_fields(tpn_xml,prog,bogusID=''):
    """
    Adds the fields that compose the 'header' of a pTPN XML file.
    """
    prog_id = ET.SubElement(tpn_xml,'id')
    prog_name = ET.SubElement(tpn_xml,'name')
    prog_features = ET.SubElement(tpn_xml,'features')

    prog_id.text = _element_id(prog)
    prog_name.text = _element_name(prog)

    #HACK: this is only necessary because we are forced to have a start event
    #for a TPN. In the future, this requirement should be removed.
    prog_start = ET.SubElement(tpn_xml,'start-event')
    if prog.first_event!=None:
        prog_start.text = _element_id(prog.first_event)
    else:
        prog_start.text = bogusID

    if prog.last_event!=None:
        prog_end = ET.SubElement(tpn_xml,'end-event')
        prog_end.text = _element_id(prog.last_event)


def export_temporal_event(temp_event):
    """
    Generates the portion of a pTPN file corresponding to a temporal event that
    is not a choice.
    """
    ev_xml = ET.Element('event')
    ev_id = ET.SubElement(ev_xml,'id')
    ev_name = ET.SubElement(ev_xml,'name')

    ev_id.text = _element_id(temp_event)
    ev_name.text = _element_name(temp_event)

    ev_xml.append(export_guard(temp_event.support))

    return ev_xml


def export_temporal_constraint(tc):
    """
    Generates the portion of a pTPN file corresponding to a temporal constraint.
    """
    tc_xml = ET.Element('temporal-constraint')
    tc_id = ET.SubElement(tc_xml,'id')
    tc_name = ET.SubElement(tc_xml,'name')
    tc_xml.append(export_guard(tc.support))
    tc_to_event = ET.SubElement(tc_xml,'to-event')
    tc_from_event = ET.SubElement(tc_xml,'from-event')
    tc_xml.append(export_duration(tc))

    tc_id.text = _element_id(tc)
    tc_name.text = _element_name(tc)
    tc_from_event.text = _element_id(tc.start)
    tc_to_event.text = _element_id(tc.end)

    return tc_xml


def export_episode(episode):
    """
    Generates the portion of a pTPN file corresponding to an episode.
    """
    ep_xml = ET.Element('episode')
    ep_id = ET.SubElement(ep_xml,'id')
    ep_name = ET.SubElement(ep_xml,'name')
    ep_xml.append(export_guard(episode.support))
    ep_to_event = ET.SubElement(ep_xml,'to-event')
    ep_from_event = ET.SubElement(ep_xml,'from-event')
    ep_xml.append(export_duration(episode.duration))
    ep_dispatch = ET.SubElement(ep_xml,'dispatch')
    ep_xml.append(export_state_constraints(episode.all_state_constraints))

    ep_id.text = _element_id(episode)
    ep_name.text = _element_name(episode)
    ep_from_event.text = _element_id(episode.start)
    ep_to_event.text = _element_id(episode.end)
    ep_dispatch.text = str(episode.action)

    return ep_xml


def export_choice(choice):
    """
    Generates the portion of a pTPN file corresponding to a choice (controllable
    or not).

    HACKED! This function includes a hack to work with the current TPN schema,
    which should be modified to allow choices to be temporal events too.
    """
    c_xml = ET.Element('decision-variable')
    c_id = ET.SubElement(c_xml,'id')
    c_name = ET.SubElement(c_xml,'name')
    c_xml.append(export_guard(choice.support))
    c_type = ET.SubElement(c_xml,'type')
    c_at = ET.SubElement(c_xml,'at-event')
    c_xml.append(export_choice_domain(choice))

    c_id.text = _choice_id(choice)
    c_name.text = _choice_name(choice)
    c_at.text = _element_id(choice)
    c_type.text = choice.type

    return c_xml


def export_choice_domain(choice):
    """
    Generates the portion of a pTPN file corresponding to the domain of a
    discrete choice.
    """
    d_xml = ET.Element('domain')

    utility = choice.utility
    probability = choice.probability

    for i,val in enumerate(choice.domain):
        d_domval = ET.SubElement(d_xml,'domainval')
        d_val = ET.SubElement(d_domval,'value')
        d_val.text = str(val)

        if len(utility)>0:
            d_util = ET.SubElement(d_domval,'utility')
            d_util.text = str(utility[i])

        if len(probability)>0:
            d_prob = ET.SubElement(d_domval,'probability')
            d_prob.text = str(probability[i])

    return d_xml


def export_guard(support):
    """
    Generates the portion of a pTPN file corresponding to the set of choice
    assignments that activate (guard) some element of the plan.

    HACKED! This function includes a hack to work with the current TPN schema,
    which should be modified to allow choices to be temporal events too.
    """
    g_xml = ET.Element('guard')

    if sum([len(conj) for conj in support])==0: #Element has no support
        g_bool = ET.SubElement(g_xml,'boolean-constant')
        g_bool.text = 'true'
    else:
        g_d = ET.SubElement(g_xml,'or') #Outer disjunction
        for conj in support:
            g_cg = ET.SubElement(g_d,'guard')
            g_cga = ET.SubElement(g_cg,'and') #inner conjunction

            for assig in conj: #For each assignment in the conjunction
                g_cgag = ET.SubElement(g_cga,'guard')
                if assig.negated:
                    g_not = ET.SubElement(g_cgag,'not')
                    g_dec = ET.SubElement(g_not,'guard')
                else:
                    g_dec = g_cgag

                g_decision = ET.SubElement(g_dec,'decision-variable-equals')
                g_var = ET.SubElement(g_decision,'variable')
                g_val = ET.SubElement(g_decision,'value')
                g_var.text = _choice_id(assig.var)
                g_val.text = str(assig.value)

    return g_xml


def export_duration(duration):
    """
    Generates the portion of a pTPN file corresponding to a duration.
    """
    dur_xml = ET.Element('duration')
    if duration.type in ['controllable','uncontrollable_bounded']:
        if duration.type == 'controllable':
            dur_type = ET.SubElement(dur_xml,'bounded-duration')
        else:
            dur_type = ET.SubElement(dur_xml,'set-bounded-uncertain-duration')
        dur_low = ET.SubElement(dur_type,'lower-bound')
        dur_up = ET.SubElement(dur_type,'upper-bound')
        dur_low.text = str(duration.lb).upper()
        dur_up.text = str(duration.ub).upper()
    elif duration.type == 'uncontrollable_probabilistic':
        dur_xml.append(export_distribution(duration.distribution,'probabilistic-uncertain-duration'))
    else:
        raise TypeError('Invalid type of temporal constraint.')
    return dur_xml

def export_distribution(distribution_dict,field_name):
    """
    Exports a probability distribution written in dictionary form.
    """
    dist_xml = ET.Element(field_name)
    dist_type = ET.SubElement(dist_xml,'distribution-type')
    dist_parameters = ET.SubElement(dist_xml,'parameters')

    dist_type.text = distribution_dict['type'].upper()
    if dist_type.text in ['GAUSSIAN','NORMAL']:
        dist_type.text = 'NORMAL' #Makes sure to use NORMAL as the type
        dist_mean = ET.SubElement(dist_parameters,'parameter')
        dist_var = ET.SubElement(dist_parameters,'parameter')
        dist_mean.text = str(distribution_dict['mean'])
        dist_var.text = str(distribution_dict['variance'])
    elif dist_type.text=='UNIFORM':
        dist_lb = ET.SubElement(dist_parameters,'parameter')
        dist_ub = ET.SubElement(dist_parameters,'parameter')
        dist_lb.text = str(distribution_dict['lb'])
        dist_ub.text = str(distribution_dict['ub'])
    else:
        raise TypeError('Invalid type of probability distribution.')

    return dist_xml

def export_state(state,initial=False):
    """
    Generates the portion of a pTPN file corresponding to a state dictionary.
    """
    state_xml = ET.Element('initial-state') if initial else ET.Element('state')
    for state_var,value in state.items():
        assig_xml = ET.SubElement(state_xml,'assignment')
        state_var_xml = ET.SubElement(assig_xml,'state-variable')
        state_value_xml = ET.SubElement(assig_xml,'value')
        state_var_xml.text = _element_id(state_var)
        state_value_xml.text = str(value)
    return state_xml


def export_state_variable(state_var):
    """
    Generates the portion of a pTPN file corresponding to a state variable.
    """
    sv_xml = ET.Element('state-variable')
    sv_id = ET.SubElement(sv_xml,'id')
    sv_name = ET.SubElement(sv_xml,'name')
    sv_xml.append(export_state_variable_domain(state_var))

    sv_id.text = _element_id(state_var)
    sv_name.text = _element_name(state_var)
    return sv_xml


def export_state_variable_domain(state_var):
    """
    Generates the portion of a pTPN file corresponding to the domain of a
    state variable.
    """
    d_xml = ET.Element('domain')
    if state_var.type=='finite-discrete':
        d_domain_xml = ET.SubElement(d_xml,'finite-domain')
        for val in state_var.domain:
            d_val = ET.SubElement(d_domain_xml,'value')
            d_val.text = str(val)

    elif state_var.type=='continuous':
        d_domain_xml = ET.SubElement(d_xml,'continuous-domain')
        d_range = ET.SubElement(d_domain_xml,'range')
        d_r_lb = ET.SubElement(d_range,'lower-bound')
        d_r_ub = ET.SubElement(d_range,'upper-bound')

        d_r_lb.text = str(state_var.domain[0]) #Lower bound
        d_r_ub.text = str(state_var.domain[1]) #Upper bound
    else:
        raise ValueError('Unsupported type of state variable domain.')

    return d_xml


def export_state_constraints(state_constraints):
    """
    Generates the portion of a pTPN file corresponding to a state constraint.
    """
    sc_xml = ET.Element('state-constraint')
    sc_wff = ET.SubElement(sc_xml,'wff')
    if len(state_constraints)==0:
        sc_bool_const = ET.SubElement(sc_wff,'boolean-constant')
        sc_bool_const.text = 'true'
    else:
        sc_and_xml=ET.SubElement(sc_wff,'and')
        for sc in state_constraints:
            sc_and_wff_xml=ET.SubElement(sc_and_xml,'wff')
            if isinstance(sc,LinearStateConstraint):
                sc_and_wff_xml.append(export_linear_state_constraint(sc))
            elif isinstance(sc,AssignmentStateConstraint):
                sc_and_wff_xml.append(export_assignments_state_constraint(sc))
            else:
                raise NotImplementedError('Only linear and assignment constraints are supported as of now.')
    return sc_xml

def export_linear_state_constraint(linear_state_constraint):
    """Generates the TPN representation of a linear constraint."""
    be_xml = ET.Element('boolean-expression')
    be_cond = ET.SubElement(be_xml,'condition')
    va_cond = ET.SubElement(be_xml,'value')
    cte_va = ET.SubElement(va_cond,'constant')

    lc_str_tokens = linear_state_constraint.as_string.split()
    be_cond.text = lc_str_tokens[0]+' '+lc_str_tokens[1]
    cte_va.text = lc_str_tokens[2]
    return be_xml

def export_assignments_state_constraint(assig_state_constraint):
    """Generates the TPN representation of an assignment constraint."""
    and_xml=ET.Element('and')

    for svar,val in zip(assig_state_constraint.scope,assig_state_constraint.values):
        and_wff_xml=ET.SubElement(and_xml,'wff')
        be_xml = ET.SubElement(and_wff_xml,'boolean-expression')
        be_cond = ET.SubElement(be_xml,'condition')
        va_cond = ET.SubElement(be_xml,'value')
        cte_va = ET.SubElement(va_cond,'constant')

        be_cond.text = svar.name+'='
        cte_va.text = str(val)

    return and_xml


def export_chance_constraint(chance_constraint):
    """Generates the TPN representation of a chance constraint."""
    cc_xml = ET.Element('chance-constraint')
    cc_id = ET.SubElement(cc_xml,'id')
    cc_name = ET.SubElement(cc_xml,'name')
    cc_constraints = ET.SubElement(cc_xml,'constraints')
    cc_prob = ET.SubElement(cc_xml,'probability')

    cc_id.text = chance_constraint.id
    cc_name.text = chance_constraint.name
    cc_constraints.text = ' '.join([el.id for el in chance_constraint.constraints])
    cc_prob.text  =str(1.0-chance_constraint.risk)
    return cc_xml

def _element_id(el):
    """Returns a valid IDREF field, should one not have been provided."""
    return el.id

def _element_name(el):
    """Returns a valid name, should one not have been provided."""
    return el.name

def _choice_id(el):
    """Current pTPN's do not support choices being events, so choice nodes
    need an additional ID so that the XML is validated."""
    return _element_id(el)+'C'

def _choice_name(el):
    """Name associated to a choice ID."""
    return _element_name(el)+'C'
