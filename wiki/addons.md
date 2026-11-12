# Addons

This is not a module but the one place to explain the concept and how to utilize it. Addons in this context means that you can write your game with the framework and then allow to additively load addons, which may have their own code, i.e. from simply adding additional decks to adding expansions with its own setup procedure or dialog options. This way it would be possible to develop a game and others may provide such addons.

The major backing concept is that eveything dynamic is based on tables (e.g. simple tables as the states in the **statemachine** in `FuncSM`, or parametrized tables like for the **workflows**). Addon specific things are injected into those tables with a powerful function [`joinTree`](#joinTree).


## joinTree
* A set's `FlowSM`, `FuncsSM` and `TextsSM` are joined onto the core's by function "joinTree" (see docu in module "core") when the set is recognised (the "custom" state), before the dialog. `FlowSM` elements are addressed by id; the string form joins as its own id (so `"faction"` twice adds nothing). A set introduces a new state by adding it to `FlowSM` (`after=`/`before=`) with its function in `FuncsSM`, and replaces a state by defining the same key in `FuncsSM`.