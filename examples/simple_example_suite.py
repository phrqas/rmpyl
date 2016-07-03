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

Suite of examples using RMPyL. Should provide a somewhat comprehensive starting
point for other people's applications.

@author: Pedro Santana (psantana@mit.edu).
"""
from rmpyl.rmpyl import RMPyL
from rmpyl.defs import Event,StateVariable
from rmpyl.episodes import Episode
from rmpyl.constraints import ChanceConstraint,LinearStateConstraint,TemporalConstraint,AssignmentStateConstraint
from rmpyl.rmpylexceptions import InvalidTypeError,InconsistentSupportError
from rmpyl.execution import RMPyLTraverser
import sys

class UAV:
    """Example Python UAV class that outputs Episodes as actions."""
    def __init__(self,name):
        self._name=name

    @property
    def state(self):
        return self._on

    @state.setter
    def state(self,value):
        if isinstance(value,str) and (value.upper() in ['ON','OFF']):
            self._on=value
        else:
            raise InvalidTypeError('UAV state must be ON or OFF.')

    def fly(self,lb=3,ub=10):
        return Episode(start=Event(name=self._name+'-start-fly'),
                       end=Event(name=self._name+'-end-fly'),
                       duration={'ctype':'controllable','lb':lb,'ub':ub},
                       action='('+self._name+'-fly)')

    def scan(self,mean=5.0,var=2.0):
        return Episode(start=Event(name=self._name+'-start-scan'),
                       end=Event(name=self._name+'-end-scan'),
                       duration={'ctype':'uncontrollable_probabilistic',
                                 'distribution':{'type':'gaussian',
                                                 'mean':mean,
                                                 'variance':var}},
                       action='('+self._name+'-scan)')

    def crash(self):
        return Episode(action='('+self._name+'-crash)',terminal=True)


def rmpyl_original_verbose(hello,uav):
    """
    Implementation of the original RMPL using a more verbose syntax and adding
    a chance constraint.

    ##### Original RMPL

    class UAV {
        value on;
        value off;

        primitive method fly() [3,10];
        primitive method scan() [1,10];
    }

    class Main {
      UAV helo;
      UAV uav;

      method run () {
        [0, 18] sequence {
            parallel {
                sequence {
                    helo.scan();
                    helo.fly();
                }
                sequence {
                    uav.fly();
                    uav.scan();
                }
            }
            choose {
                with reward: 5 {helo.fly();}
                with reward: 7 {uav.fly();}
            }
        }
      }
    }
    """
    prog = RMPyL()
    prog.plan = prog.sequence(
                prog.parallel(
                    prog.sequence(
                        hello.scan(),
                        hello.fly()),
                    prog.sequence(
                        uav.fly(),
                        uav.scan())),
                prog.decide({'name':'UAV-choice','domain':['Hello','UAV'],'utility':[5,7]},
                            hello.fly(),
                            uav.fly()))
    overall_tc = prog.add_overall_temporal_constraint(ctype='controllable',lb=0.0,ub=18.0)
    cc_time = ChanceConstraint(constraint_scope=[overall_tc],risk=0.1)
    prog.add_chance_constraint(cc_time)
    return prog

def rmpyl_original_overload(hello,uav):
    """

    Implementation of the original RMPL using operator overload to simplify
    sequential and parallel compositions.

    ##### Original RMPL

    class UAV {
        value on;
        value off;

        primitive method fly() [3,10];
        primitive method scan() [1,10];
    }

    class Main {
      UAV helo;
      UAV uav;

      method run () {
        [0, 18] sequence {
            parallel {
                sequence {
                    helo.scan();
                    helo.fly();
                }
                sequence {
                    uav.fly();
                    uav.scan();
                }
            }
            choose {
                with reward: 5 {helo.fly();}
                with reward: 7 {uav.fly();}
            }
        }
      }
    }
    """
    prog = RMPyL()
    prog*= ((hello.scan()*hello.fly())+(uav.fly()*uav.scan()))*prog.decide({'name':'UAV-choice','domain':['Hello','UAV'],'utility':[5,7]},
                                                                            hello.fly(),
                                                                            uav.fly())
    overall_tc = prog.add_overall_temporal_constraint(ctype='controllable',lb=0.0,ub=18.0)
    cc_time = ChanceConstraint(constraint_scope=[overall_tc],risk=0.1)
    prog.add_chance_constraint(cc_time)
    return prog

def rmpyl_simple_verbose(hello,uav):
    """Simple RMPyL example using verbose syntax."""
    prog = RMPyL()
    prog *= prog.sequence(hello.scan(),uav.scan(),prog.parallel(hello.fly(),uav.fly()))
    return prog

def rmpyl_simple_overload(hello,uav):
    """Simple RMPyL example using overloaded operators. Note that this is not
    exactly equivalent to the previous one, since the overloaded operators can
    only combine pairs of episodes, while sequence and parallel can combine an
    arbitrary number or internal episodes."""
    prog = RMPyL()
    prog *= hello.scan()*uav.scan()*(hello.fly()+uav.fly())
    return prog

def rmpyl_simple_observe(hello,uav):
    """Simple RMPyL example using an uncontrollable choice."""
    prog = RMPyL()
    prog *= prog.observe({'name':'UAV-crash','ctype':'probabilistic',
                          'domain':['OK','FAULT'],'probability':[0.99,0.01]},
                        uav.scan(),
                        uav.crash())
    return prog


def rmpyl_simple_nested_choice(hello,uav):
    """Simple RMPyL example with nested choice."""
    prog = RMPyL()
    prog *= prog.decide({'name':'UAV-choice1','domain':['H','U'],'utility':[5,7]},
                         prog.decide({'name':'UAV-choice2','domain':['H','U'],'utility':[5,7]},
                            hello.fly(),uav.fly()),
                         uav.scan())
    return prog

def rmpyl_double_nested_choice(hello,uav):
    """Simple RMPyL example with nested choices."""
    prog = RMPyL()
    prog *= prog.decide({'name':'UAV-choice1','domain':['H','U'],'utility':[5,7]},
                         prog.decide({'name':'UAV-choice2','domain':['H','U'],'utility':[5,7]},
                            hello.fly(),uav.fly()),
                         prog.decide({'name':'UAV-choice3','domain':['H','U'],'utility':[5,7]},
                            hello.fly(),uav.fly()))
    return prog


def rmpyl_parallel_choices(hello,uav):
    """Simple RMPyL example with parallel execution of choices."""
    uav2 = UAV(name='uav2')

    prog = RMPyL()
    prog *= prog.parallel(
                prog.observe({'name':'HELLO-OBS','domain':['FLY','SCAN','CRASH'],
                          'ctype':'probabilistic','probability':[0.50,0.49,0.01]},
                           hello.fly(),hello.scan(),hello.crash()),
                prog.observe({'name':'UAV-OBS','domain':['FLY','SCAN','CRASH'],
                          'ctype':'probabilistic','probability':[0.50,0.49,0.01]},
                           uav.fly(),uav.scan(),uav.crash()))*uav2.fly()
    return prog


def rmpyl_simple_iteration(hello,uav,sequence):
    """Example of how we can combine RMPyL and Python commands to simulate a
    a function being repeatedly executed."""

    def make_fly_scan(hello,uav):
        """Subplan where one choose which UAV should fly and which should scan."""
        p_fly_scan = RMPyL()
        p_fly_scan*= p_fly_scan.decide({'name':'Choose-FLY','domain':['H','U'],'utility':[5,7]},
                                        hello.fly()+uav.scan(),
                                        hello.scan()+uav.fly())
        return p_fly_scan

    loop_prog = RMPyL()
    if sequence:
        for i in range(3): #Combines subprogs in sequence
            loop_prog*= make_fly_scan(hello,uav)
    else:
        for i in range(3): #Combines subprogs in parallel
            loop_prog+= make_fly_scan(hello,uav)

    return loop_prog

def rmpyl_parallel_user_defined_tcs(hello,uav):
    """Simple RMPyL example with parallel execution of actions with user-defined
    constraints."""
    prog = RMPyL()
    hello_flight = hello.fly()
    uav_flight = uav.fly()
    uav_scan = uav.scan()
    prog *= hello_flight+(uav_scan*uav_flight)

    tc1 = TemporalConstraint(start=uav_scan.end,end=hello_flight.start,
                             ctype='controllable',lb=2.0,ub=3.0)

    tc2 = TemporalConstraint(start=hello_flight.end,end=uav_flight.start,
                             ctype='controllable',lb=3.0,ub=4.0)
    for tc in [tc1,tc2]:
        prog.add_temporal_constraint(tc)

    prog.add_overall_temporal_constraint(ctype='controllable',lb=0.0,ub=50.0)

    return prog

def rmpyl_parallel_and_choice_user_defined_tcs(hello,uav):
    """Simple RMPyL example with parallel execution of actions on different choice
    branches with user-defined constraints."""
    prog = RMPyL()

    #Choice using the previous example as a subroutine to generate partial progs
    prog *= prog.decide({'name':'Choose-branch','domain':['1','2'],'utility':[1,2]},
                        rmpyl_parallel_user_defined_tcs(hello,uav),
                        rmpyl_parallel_user_defined_tcs(hello,uav))

    prog.add_overall_temporal_constraint(ctype='controllable',lb=0.0,ub=70.0)

    return prog

def rmpyl_inconsistent_user_defined_tcs(hello,uav):
    """Simple RMPyL example with parallel execution of actions on different choice
    branches with user-defined constraints."""
    try:
        prog = RMPyL()
        hello_flights = [hello.fly() for i in range(2)] #two different hello flights
        uav_flights = [uav.fly() for i in range(2)] #two different uav flights

        #Choice using the previous example as a subroutine to generate partial plans
        prog *= prog.decide({'name':'Choose-branch','domain':['1','2'],'utility':[1,2]},
                            hello_flights[0]*uav_flights[0],
                            uav_flights[1]*hello_flights[1])

        tc = TemporalConstraint(start=hello_flights[0].end,end=hello_flights[1].start,
                                 ctype='controllable',lb=2.0,ub=3.0)

        #This is a constraint between disjoint plan branches. Therefore, it MUST
        #cause an error of empty constraint support
        prog.add_temporal_constraint(tc)
    except InconsistentSupportError:
        print('Empty support error correctly caught!')
        prog=None

    return prog

def rmpyl_simple_decide_looping(hello,uav):
    """Simple RMPyL example where we choose to fly loops with different UAVs."""
    prog = RMPyL()
    prog *= prog.decide({'name':'Choose-loop','domain':['H','U'],'utility':[1,1]},
                        prog.loop(episode_func=hello.fly,repetitions=3,
                                  run_utility=1,stop_utility=0),
                        prog.loop(episode_func=uav.scan,repetitions=2,
                                  run_utility=2,stop_utility=0))
    return prog

def rmpyl_single_episode(hello,uav):
    """Extremely simple plan composed of a single primitive episode."""
    prog = RMPyL()
    prog.plan = uav.scan()
    healthy = StateVariable(name='Healthy',
                           domain_dict={'type':'finite-discrete',
                                        'domain':['True','False','Maybe']})

    assig_sc = AssignmentStateConstraint(scope=[healthy],values=['True'])
    prog.add_overall_state_constraint(assig_sc)
    return prog

def rmpyl_episode_ids(hello,uav):
    """Example of how episode ID's can be used to retrieve them."""
    prog = RMPyL()

    first_uav_seq = prog.sequence(uav.scan(),uav.fly(),id='uav-1-seq')
    second_uav_seq = prog.sequence(uav.scan(),uav.fly(),id='uav-2-seq')

    first_hello_seq = prog.sequence(hello.scan(),hello.fly(),id='hello-1-seq')
    second_hello_seq = prog.sequence(hello.scan(),hello.fly(),id='hello-2-seq')

    prog *= prog.parallel(prog.sequence(first_uav_seq,second_uav_seq,id='uav-seqs'),
                          prog.sequence(first_hello_seq,second_hello_seq,id='hello-seqs'),id='par-seqs')

    #This could have been accomplished much more easily by using the sequence
    #variables directly, but I wanted to show how episodes can be retrieved by
    #ID.
    tc1 = TemporalConstraint(start=prog.episode_by_id('uav-1-seq').end,
                            end=prog.episode_by_id('hello-2-seq').start,
                            ctype='controllable',lb=2.0,ub=3.0)

    tc2 = TemporalConstraint(start=prog.episode_by_id('hello-1-seq').end,
                            end=prog.episode_by_id('uav-2-seq').start,
                            ctype='controllable',lb=0.5,ub=1.0)

    prog.add_temporal_constraint(tc1)
    prog.add_temporal_constraint(tc2)

    return prog

def rmpyl_state_constraints(hello,uav):
    """
    Examples showing how state variables and constraints can be added to RMPyL.
    """
    prog = rmpyl_original_verbose(hello,uav)

    healthy = StateVariable(name='Healthy',
                           domain_dict={'type':'finite-discrete',
                                        'domain':['True','False','Maybe']})

    c1_svar = StateVariable(name='C1',
                            domain_dict={'type':'continuous',
                                        'domain':[0,100]})

    c2_svar = StateVariable(name='C2',
                            domain_dict={'type':'continuous',
                                        'domain':[0,100]})

    lin_sc=LinearStateConstraint(scope=[c1_svar,c2_svar],coef=[3,-4],rel='=',rhs=2.0)
    assig_sc = AssignmentStateConstraint(scope=[healthy],values=['True'])
    prog.add_overall_state_constraint(lin_sc)
    prog.add_overall_state_constraint(assig_sc)

    cc_state = ChanceConstraint(constraint_scope=[lin_sc,assig_sc],risk=0.1)
    prog.add_chance_constraint(cc_state)

    prog.initial_state = {healthy:'True',c1_svar:10}
    return prog

def run_example(option,write_tpn=True):
    """Runs one of the defined examples."""
    if option==1:
        prog = rmpyl_original_verbose(hello,uav)
    elif option==2:
        prog = rmpyl_original_overload(hello,uav)
    elif option==3:
        prog = rmpyl_simple_verbose(hello,uav)
    elif option==4:
        prog = rmpyl_simple_overload(hello,uav)
    elif option==5:
        prog = rmpyl_simple_observe(hello,uav)
    elif option==6:
        prog = rmpyl_simple_nested_choice(hello,uav)
    elif option==7:
        prog = rmpyl_double_nested_choice(hello,uav)
    elif option==8:
        prog = rmpyl_parallel_choices(hello,uav)
    elif option==9:
        prog = rmpyl_simple_iteration(hello,uav,sequence=True)
    elif option==10:
        prog = rmpyl_simple_iteration(hello,uav,sequence=False)
    elif option==11:
        prog = rmpyl_parallel_user_defined_tcs(hello,uav)
    elif option==12:
        prog = rmpyl_parallel_and_choice_user_defined_tcs(hello,uav)
    elif option==13:
        prog = rmpyl_inconsistent_user_defined_tcs(hello,uav)
    elif option==14:
        prog = rmpyl_simple_decide_looping(hello,uav)
    elif option==15:
        prog = rmpyl_single_episode(hello,uav)
    elif option==16:
        prog = rmpyl_episode_ids(hello,uav)
    elif option==17:
        prog = rmpyl_state_constraints(hello,uav)
    else:
        print('Please choose an integer between 1 and 17 (or 0 to run all examples).')
        sys.exit(0)

    if prog!=None and prog.plan!=None:

        print('\n***** Start event\n')
        print(prog.first_event)

        print('\n***** Last event\n')
        print(prog.last_event)

        print('\n***** Primitive episodes\n')
        for i,p in enumerate(prog.primitive_episodes):
            print('%d: %s\n'%(i+1,str(p)))

        print('\n***** Events\n')
        for i,e in enumerate(prog.events):
            print('%d: %s'%(i+1,str(e)))

        rmpyl_traverse = RMPyLTraverser(prog)

        print('\n*****Initially active choices\n')
        print(', '.join(['%s (%s)'%(c.name,c.id) for c in rmpyl_traverse.initially_active_choices]))

        print('\n***** Choice activation dictionary\n')
        for choice,activation_dict in rmpyl_traverse.choice_activation_dict.items():
            for assig_tuple,activation_list in activation_dict.items():
                assig_str = 'NOT %s'%(str(assig_tuple[0])) if assig_tuple[1] else str(assig_tuple[0])
                active_choice_str=', '.join(['%s (%s)'%(c.name,c.id) for c in activation_list])
                print('%s (%s)=%s->[%s]'%(choice.name,choice.id,assig_str,active_choice_str))

        print('\n***** Temporal constraints\n')
        for i,tc in enumerate(prog.temporal_constraints):
            print('%d: %s\n'%(i+1,str(tc)))

        print('\n***** State constraints\n')
        for i,sc in enumerate(prog.state_constraints):
            print('%d: %s\n'%(i+1,str(sc)))

        print('\n***** Chance constraints\n')
        for i,cc in enumerate(prog.chance_constraints):
            print('%d: %s\n'%(i+1,str(cc)))

        if write_tpn:
            prog.to_ptpn(filename='rmpyl_ptpn.tpn')
    else:
        print('Empty RMPyL program.')


if __name__=='__main__':

    hello = UAV(name='hello')
    uav = UAV(name='uav')

    if len(sys.argv)!=2:
        print('Please choose an integer between 1 and 17 (or 0 to run all examples).')
    else:
        option = int(sys.argv[1])

        if option==0: #Runs all examples
            for ex in range(1,18):
                run_example(ex,write_tpn=False)
        else:
            run_example(option)
