# RMPyL - a Python implementation of RMPL

The goal of RMPyL is to extend the Python programming language with the same constructs and operators originally proposed for RMPL (Reactive, Model-based Programming Language) that allow the desired behavior of autonomous systems to be specified at a high-level of abstraction. It is not a compiler for RMPL written in Python! Instead, RMPyL is a module that allows Python to be used to "program" the behavior of autonomous systems in terms of desired state, rather than low-level, application-dependent commands. How cool is that?!

## Why RMPyL?

The historical development of RMPL as a standalone programming language made its widespread adoption a challenge, for this requires support to several advanced features that have become standard in most modern programming languages. In any case, RMPL's original goal of elevating the level of interaction between mission operators and autonomous systems still stands as a worthy, significant contribution.

RMPyL addresses this issue by extending Python, a widely used general-purpose programming language, with the core constructs from the original proposal of RMPL, therefore closing the gap between the ideas behind RMPL and their actual implementation. A non-exhaustive list of RMPyL features:

  * RMPyL is a Python module. Therefore, anything available in Python can be used to manipulate RMPyL objects, such as list comprehensions, dictionaries, recursion, file I/O, network interfaces, and ROS (Robot Operating System);

  * RMPyL only depends on the availability of a Python interpreter (2 or 3) and its standard libraries, which means it is cross-platform; 

  * RMPyL is useful both for sequencing (programmatically describe a temporal plan), as well as for modeling;

  * RMPyL is built around the concept of episodes and their sequence, parallel, and choice compositions (see description below). Since an RMPyL program is also represented as an episode, it is very easy to write libraries of RMPyL subroutines that can be composed to form more complex RMPyL programs;

  * RMPyL can be used for automatic generation of control programs (e.g., pKirk outputs its optimal execution policies with sensing actions as RMPyL programs);

  * RMPyL programs can be readily exported to Enterprise-compatible TPN's. More specifically, it generates Probabilistic Temporal Plan Networks (pTPN's), which feature controllable and uncontrollable (probabilistic) choices, as well as uncontrollable temporal durations;

  * RMPyL performs automatic propagation of constraint and episode guards.
  
## Installation

RMPyL is a lightweight module for Python 2 and 3 with no dependencies beyond the standard libraries. It is officially hosted at

  git@git.mers.csail.mit.edu:enterprise/RMPyL.git

In order to install it in your default path for Python packages, just issue

  python setup.py install 

Alternatively, you can also just decompress it somewhere in your PYTHONPATH.   
  
  
