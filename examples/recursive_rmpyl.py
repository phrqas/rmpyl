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

Implementation of recursive.rmpl using RMPyL.

##### recursive.rmpl

class Result {
    value success;
    value fail;
}

class Robot {
    Result result;

    primitive method do_action() [1, 2];
    primitive method give_up() [1, 2];

    method try_try_again() {
        {
            do_action();
            if (result == fail) {
                {
                    choose {
                        with choice: try_try_again();
                        with choice: give_up();
                    }
                }
            }
        }
    }
}

class Main() {
    Robot r;

    method run() {
        [0, 10] r.try_try_again();
    }
}

@author: Pedro Santana (psantana@mit.edu).
"""
from rmpyl.rmpyl import RMPyL, Episode
from rmpyl.rmpylexceptions import InvalidTypeError
import sys

class Robot(object):
    """
    Python class representing a robot. It interacts with RMPyL by generating
    Episodes as output.
    """
    def __init__(self,name,achieved_goal=False):
        self._name=name
        self._achieved_goal=achieved_goal

    @property
    def achieved_goal(self):
        return self._achieved_goal

    @achieved_goal.setter
    def achieved_goal(self,achievement_flag):
        if isinstance(achievement_flag,bool):
            self._achieved_goal= achievement_flag
        else:
            raise InvalidTypeError('Achievement flag must be a Boolean.')

    def do_action(self):
        return Episode(duration={'ctype':'controllable','lb':1,'ub':2},
                       action=self._name+'-do-action()')

    def stop(self):
        return Episode(action=self._name+'-stop()')

def try_try_again(prog,action_func,halt_func,loop_utility,stop_utility,repetitions):
    if repetitions<=0:
        return halt_func()
    else:
        return prog.decide({'name':'loop-choice-'+str(repetitions),
                            'domain':['RUN','HALT'],
                            'utility':[loop_utility,stop_utility]},
                    prog.sequence(
                        action_func(),
                        prog.observe({'name':'observe-success-'+str(repetitions),
                                     'ctype':'uncontrollable','domain':['SUCCESS','FAIL']},
                            halt_func(),
                            try_try_again(prog,action_func,
                                          halt_func,loop_utility,stop_utility,
                                          repetitions-1))),
                    halt_func())


prog = RMPyL()
rob = Robot(name='ResilientRobot')

repetitions = int(sys.argv[1]) if len(sys.argv)==2 else 3

prog*= try_try_again(prog,rob.do_action,rob.stop,loop_utility=1,
                     stop_utility=0,repetitions=repetitions)
prog.add_overall_temporal_constraint(ctype='controllable',lb=0.0,ub=10.0)


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

# print('\n***** Event successors\n')
# for i,(ev,successors) in enumerate(prog.event_successors.items()):
#     print('%d: %s -> %s'%(i+1,ev.name,str([e.name for e in successors])))

print('\n***** Temporal constraints\n')
for i,tc in enumerate(prog.temporal_constraints):
    print('%d: %s\n'%(i+1,str(tc)))

prog.to_ptpn(filename='recursive_rmpyl_ptpn.tpn')
