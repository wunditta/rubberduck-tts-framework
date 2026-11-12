# State Machine

The state machine (SM) is a generic flow control framework and is most usefule in cases where player inputs (e.g. dialogs) and scripted object manipulation intervene, which is typical for a setup procedure. The SM is implemented as a table of state functions (`FuncsSM`, one function per state) and a default order (see `FlowSM`). A state does its work, then either the next state in the default order runs, or the state defines a different state to run next. In addition the trigger for the next state can be defined, i.e. immediately, waiting for a trigger (e.g. pushing a button, hotkey, dialog button), etc.

This and many other modules are designed to allow addons to be loaded into the game (e.g. additional card decks or a whole new expansion). Addons can have their own code and can integrate into the core code without the need to change it (e.g. new states for the SM, additional steps in a setup procedure, or even a completely different setup procedure). For more info see [**`addons`**](addons.md).

This is a module of the "Rubberduck TTS Framework" and depends on these other modules: [**`core`**](core.md)

## Preferences
Use `setPref` and `getPref` (see [`core`](core.md#prefsRTF)) to set and retrieve the preferences.

| Path | Description
|---|---|
| [`sm.flowpresets`](#sm.flowpresets) | A table with nested keyed tables, which define a preset for `addExceptionSM` and the return value of a `FuncsSM` function.

### sm.flowpresets<a name="sm.flowpresets"></a>
Certain combinations of the parameters for advancing through the SM are used frequently. Here you can define preset combinations and refer to them by their name (key).

For each nested table the key is an id/name and the value is a combination of the [**state parameters**](#stateinfo) and the parameters for function [`addExceptionSM`](#addExceptionSM) (you must use named parameters). If used as return value for a `FuncsSM` function the exception parameters are ignored. By default the following presets are defined:

```lua
sm.flowpresets = {
  back = {severity=2, next=false},
  auto = {restart=true, onload=false},
  hold = {advance=false, restart=false, onload=false},
  finish = {next=-1, advance=false, restart=false, onload=false}
}
```

## Member Variables

| Variable | Description | Type
|---|---|---|
| [`FlowSM`](#defaultflow) | A table of strings or tables, specifying the default order of the states | [{string/func}]
| [`FuncsSM`](#FuncsSM) | A table of state functions, one for each state: `FuncsSM.setup = function(ctx) … end`. | [{func}]
| [`TextsSM`](#TextsSM) | A table with a subtables with texts to be shown before and after each state | [{tab}]

### FuncsSM<a name="FuncsSM"></a>
The table holding all state functions, i.e. when the SM is triggered the function with the name equal to the **current state** is called. The "ids" in the default flow defined in `FlowSM` must also reference to the same names.
* Function definition: `FuncsSM.<name> = function(stateinfo [tab]) ... return "preset" end`
* States are run inside a coroutine, thus they run in parallel to the rest of the code.
* A state must not call `runSM` itself, if the next state should be started immediately use `setFlowSM{restart=true}`.

#### Parameters
Parameter given to each function: For convenience a table `{prev=, state=, speed=}` is provided (info taken from `getStateSM` (second return) and the speed parameter from `runSM`.

#### Return
For convenience the flow can be defined with a [`flowpreset`](#sm.flowpresets) as return value (instead of using `setFlowSM`). Also see [`Flow Control`](#flowcontrol).

#### Example
```lua
FlowSM = {"init", "setup"}
FuncsSM = {
  ["init"] = function(stateinfo)
    ...
  end,
  ["setup"] = function(stateinfo)
    ...
    return "back" -- the SM will go back to the state previously run
  end
}
```

### TextsSM<a name="TextsSM"></a>



```lua
TextsSM = {
    textsObjectSM = "guid",
    textsOffsetSM = vector(0, 0, 0),
    init={
        prev= {"Scripted Setup - Press Button", "The setup is done step-by-step"}
        },
    setup={
        prev= {"- Standby -", "Suggested elements are being placed."},
        after= {"Finalize Setup", "Optional: Change or remove randomly placed items on the board."}
        },
}
```

## Function Summary
| Function | Description | Return | prefsRTF
|---|---|---|---|
| [`addExceptionSM(!!!!!!!!!)`](#addExceptionSM) | Registers an exception (notification, warning, or error) which can display a dialog and may also define how the SM will advance. Also see [Exceptions](#Exceptions). | - | -
| [`getExceptionSM()`](#getExceptionSM) | Returns 1) the history (exceptions) as table of sub-tables (one for each exception: `{type=, description=, severity=, special=}`), and 2) the highest severity rating of all exceptions. | [{tab}], [num] | -
| [`getFlagSM()`](#flags) | 
| `getFlowIndexSM(state=current state [str])` | Returns the index number of the specified (or current) state within `FlowSM`.<br>* `false`: If not found<br>* `0`: SM never run<br>* `-1`: SM finished | [num] | -
| `getFlowNameSM(stateindex=current state [num])` | Returns the id (name) of the specified (or current) state within `FlowSM`.<br>* `false`: If index is out of bounds<br>* `""`: if SM never run or is finished | [str] | -
| [`getStateSM()`](#flowcontrol) | Returns 1) the "current state" (string) and 2) a table with all [`state parameters`](#stateinfo) `{prev, state, next, advance, restart, onload}`. | [str], [tab] | -
| `isLockedSM()` | Returns `true` if the SM is currently locked, i.e. `smRun` will do nothing. Usually this is while the SM is running (main exceptions are dialogs).
| `isOrAfterFlowSM(state [str])` | Returns `true` if current state is equal to or past the specified state within `FlowSM`, `false` if it is before. Returns `nil` if either the current or the specified states are not found in `FlowSM`. | [bool] | -
| `isRunningSM()` | Returns `true` if a state is currently running, false if in sleep mode. | [bool] | -
| `isFinishedSM()` | Returns `true` if the last state has run (SM is permanently inactive). | [bool] | -
| `lockSM()` | If used while a state is running it serves as a flag to keep the SM locked after the state has finished (e.g. for dialogs). If used while in sleep mode the SM is locked, so a new state cannot be started. | - | -
| [`setFlagSM()`](#flags) | 
| [`setFlowSM(next [str], advance [bool], restart [bool/num], onload [bool])`](#stateinfo) | This is the only way you should use to set the next state or to control the flow (except for return value of `FuncsSM` function). Any specified parameter (not nil) will override any default values (e.g. `FlowSM`) when the next state is determined (forced behavior). | - | -
| [`runSM(speed [num])`](#flowcontrol) | Runs the current state's function (`FuncsSM`) in a coroutine. This is the only way to start the SM. The state is only run, if no other state is currently running. After the state has finished the next state may be called immediately depending on `speed`. | - | -
| `unlockSM()` | Unlocks the SM so a new state can be started. Note: Only use this if no state is running, otherwise this will be ignored. Returns `true` if the lock was successful, otherwise `false`. | [bool] | -

## Function Details

### addExceptionSM(...)<a name="addExceptionSM"></a>
This should work like todays addUIStateException. Description can mostly taken from this.

#### Parameters
* **``**:

#### Return
* **``**:

## Flow Control<a name="flowcontrol"></a>

### Principles
* Like all state machines only one state is the "current state" at any given time, and only one state can run at any given time.
* This state machine can be in sleep mode, where no state is running and the SM waits to be started again.
* Immediately after a state has finished the state is advanced (so in sleep mode the current state is the one which will be run if the SM is triggered), therefore the "current state" is:
  * Active: If the state is running.
  * Pending: If the SM is asleep (does not run). The current state is run the next time the SM is triggered.
* Each state defines the next state to run. In addition, for a mostly linear default flow it is possible to define the flow upfront (`FlowSM`).

### State Parameters<a name="stateinfo"></a>
The following parameters are central for the SM and hold the state info and info how the SM should advance.
* **`prev`** [string]: The id (name) of the previously run state (may not follow the order in `FlowSM`).
* **`state`** [string]: The id (name) of the current state.
* **`next`** [str/num/bool]: Specifies the next state to run:
  * "id" [str]: The id/name of the state, i.e. the name of a `FuncsSM` function.
  * `false` [bool]: Will return to the previously run state (which not neceassarily is the one before in `FlowSM`).
  * `-1/0/1+` [num]: A positive number will set the corresponding state in `FlowSM`; 0 resets the SM (as if never ran); -1 finishes the SM (no state function will be called by `runSM`).
* **`advance=true`** [bool]: After finishing the current state the SM should advance to the next state (true), or keep the current otherwise.
* **`restart=false`** [bool/num}: This defines if the SM should be run again after this state has finished, i.e. after the next state was set the machine is started and will run the next state immediately
  * `true/false` [bool]: True will always continue, false will wait (default).
  * `1+` [num]: The SM will be started automatically if the current speed is ≥ n, i.e. n is the **minimum** number `flowspeedSM` has to be to restart the SM automatically (in other words: the higher n is, the higher the speed needs to be to run it automatically). (Note: `0` would behave the same way as `true`.)
* **`onload=false`** [bool]: After a game load the machine continues with the current state. Default is false: after a load the machine waits for a trigger.

| SM Status | State Info | Example
|---|---|---|
| Sleep | * `prev`: The previously finished state.<br>* `state`: Id of the current state, i.e. the one which will be run upon trigger.<br>* `next=nil`<br>* `advance=nil`<br>* `restart=nil`<br>* `onload`: true or false depending on settings. | * `prev="init"`<br>* `state="setup"`<br>* `next=nil`<br>* `advance=nil`<br>* `restart=nil`<br>* `onload=true`
| Running Start | * `prev`: The previously finished state.<br>* `state`: Id of the currently run state.<br>* `next=nil`<br>* `advance=nil`<br>* `restart=nil`<br>* `onload=nil` | * `prev="init"`<br>* `state="setup"`<br>* `next=nil`<br>* `advance=nil`<br>* `restart=nil`<br>* `onload=nil`
| Running End | * `prev`: The previously finished state.<br>* `state`: Id of the currently run state.<br>* `next`: may be set now<br>* `advance`: may be set now<br>* `restart`: may be set now<br>* `onload`: may be set now | * `prev="init"`<br>* `state="setup"`<br>* `next="dialog"`<br>* `advance=true`<br>* `restart=true`<br>* `onload=false`
| State ended | The new state is determined (by above set `next`, `advance`, `restart`, and/or `FlowSM`) and the variables are set:<br>* `prev`: The id of the just finished state.<br>* `state`: Id of the now current state.<br>* `next=nil`: is now reset<br>* `advance=nil`: is now reset<br>* `restart=nil`: is now reset<br>* `onload`: may be set now | * `prev="setup"`<br>* `state="dialog"`<br>* `next=nil`<br>* `advance=nil`<br>* `restart=nil`<br>* `onload=false`<br>Next state will be started immediately as `restart` was set to `true` before (`false` would set the SM to sleep).

### Flow Mechanism
* If the game is loaded and the current state is set to be run upon load (`onload=true`) the SM is started, otherwise it will be in sleep mode.
* Running the current state with `runSM(speed)`:
  * The **first time** the SM is started there is no current state. If `FlowSM`is
    * defined: the first state from it is run
    * not defined: A state function `init`must exist as this one is called.
  * **Before** the state function is started:
    * the SM is locked (can be checked with `isLockedSM()`) to prevent running multiple states at once.
    * the `onload` parameter is not needed anymore and set to `nil`.
  * The state function (`FuncsSM`) is started within a **coroutine**. *(If you are new to this concept: this means the state code runs in parallel to the other code, i.e. TTS will also continue to execute the code after the `runSM` call.)*
* Within the coroutine the SM waits until the state function has **ended**. Immediately after it ended:
  * Sets the **next state** depending on the state parameters (using `advanceStateSM`):
    * either it was specified within the finished state (with `setFlowSM`)
    * or by returning a [`flowpresets`](#sm.flowpresets) name
    * or the next state in `FlowSM` is taken
    * or the SM is set to finished (permanently ended)
  * Unlocks the SM, unless a dialog is shown (see module [**dialog**](dialog.md)), as it should not be possible to trigger the next state before the dialog is closed. The SM keeps being locked if:
    * If the state was started with `FlowSM` defaults (if the key "dialog" was used)
    * Calling [`showDLG`](dialog.md#showDLG) within the state to show the dialog
    * If you start a dialog by your own code then you should use `lockSM` to keep the SM locked while the dialog is open. Upon ending the dialog make sure to use `unlockSM`.
* If `restart` is enabled the next state may **immediately** be run:
  * `true`: is run in any case
  * `1+`: if the provided `speed` value (with `runSM`) ≥ `restart` value
* Otherwise the SM ends for now (**sleep mode**) and waits:
  * to be started again (calling `runSM`) with e.g. the press of a button
  * upon loading the game if `onload` is true

### Default Flow<a name="defaultflow"></a>

```lua
FlowSM = {{name="init", onload=true, restart=true}, {name="custom", restart=1}, "faction", {name="manual", restart=1}, "dialog", "setupboard", {name="mainboard", restart=true}, "cleanup"}
```

The default flow is specified in "FlowSM", which is a list of the states in order. Each element is provided in one of two ways:
* `"name"`: A string, which is the state name or id (is equal to `{id="name"}`)
* `{id="name", ...}`: A table with these parameters:
  * `id`: The state name.
  * `advance`/`restart`/`onload`: See [state parameters](#stateinfo) for description.
  * `dialog="panelid"` (requires the "dialog" module): The state shows this dialog and waits (SM stops, keeps the current state, and waits for a trigger from one of the dialogs buttons). If "OK" the next state becomes the current and the SM is called (as normally something should happen after a dialog was confirmed). "Cancel" closes the dialog, stays with the current state and waits again). For simple cases no function in "FuncsSM" is needed. However, a function can be defined and is called before the dialog is shown (so things happen in the background while the dialog is shown).
  * `workflow="phase" or true` (requires the "workflow" module): This depends on how the workflows are implemented. The value is forwarded to the workflow caller function. If only one workflow is defined then "true" will start it, otherwise the value defines which workflow to run. No "FuncsSM" function will be called (even if present).
  * `text="key"`: The `TextsSM` key if it differs from the state name.

### Exceptions(...)<a name="Exceptions"></a>
General explanation of the concept....
Similar to current, but flow parameters are set according to severity (equal or higher overrules lower)

* Exceptions: `addExceptionSM(kind, level, text)` — collected while a state runs, evaluated when it returns: `kind="hold"` → the machine waits for a trigger, whatever the speed (the players fix something), `kind="goback"` → the previous state runs again; `level="error"|"note"` decides the colour and whether the texts are shown in a dialog or only in the chat *(decide)*. The texts are shown through a callback the dialog module registers (`registerShowSM(fn)`); the machine itself prints nothing. Today's `addUIStateException`, `getUIStateExceptions`, `removeUIStateExit`.

### Flags<a name="flags"></a>
Shoul not be here, but as normal function description in the table
* Flags: `flagSM(name, value)` / `flagSM(name)` — booleans that survive a load (in the record), cleared by `resetSM` (today's `setUIFlag`/`getUIFlag`, e.g. `cardmats`, `startdeck`, `qm_role`).

### Example
Let's assume the players selected a special option in state A, which requires them to do something manually on the board. Before you continue with the normal setup (state B) you want to check if this was done. There are two options:

#### Additional State Function
Add an additional state function C, which performs the check and continues with B. It is not included in `FlowSM`, but A sets C as next state if the option was chosen, otherwise C is left out.

```lua
FlowSM = {"A", "B"}
FuncsSM = {
  ["A"] = function
    --...
    if special_option then setFlowSM{next="C"} end
    --...
  end,
  ["B"] = function --[[...]] end,
  ["C"] = function
    --...
    if check_ok then setFlowSM{next="B", restart=true}
    else
      -- error code
      setFlowSM{advance=false} -- state stays in C until check is OK
    end
  end
}
```

#### Flag and Rerun the same State
In case you could reuse some code from state A for the check you would not want to copy it to C. Instead set a flag and do not advance the state, so that A is rerun, and because of the flag A knows that now it should perform the check.

```lua
FuncsSM = {
  ["A"] = function
    --...
    if getFlagSM("special") then
      -- error code
      setFlagSM("special", true, false) -- clears the flag
    end
    --...
    if special_option then
      setFlagSM("special", true) -- sets this flag for current state
      setFlowSM("A") 
    end
  end
}
```


# Internal

## Member Variables
| Variable | Description | Type
|---|---|---|
| `lockedSM` | Is true if the SM is running, otherwise false (is used for `isRunningSM`). | [bool]
| `persistSM` | A **persistent** [(see module **core**)](core.md#PersistentDataRTF) table to store data for the SM. | [tab]
| [`persistSM.state = {prev, state, next, advance, restart, onload}`](#persistSM.state) | All info for the current state. | [tab]

### persistSM.state<a name="persistSM.state"></a>

## Function Summary
| Function | Description | Return | prefsRTF
|---|---|---|---|
| `advanceStateSM(speed [num])` | The code actually determining the next state (and may also call runSM() if restart~=false). It needs to be a separate function as it is called by runSM() after a state is finished and by a dialog when pressing OK. | - | -
| `onSaveLoadFuncsRTF.statemachine(event [str])` | Runs the the SM if the current state has `onload=true` (the function has `onSaveLoadFuncsRTF.order.statemachine = 190`). | - | -

## Functions

### advanceStateSM(...)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Advances to the next state. This should only be called by runSM after a state has finished.
* **`advance=true`** [bool]: If true the current (pending) state is set to `next` or to the next state as defined in `FlowSM`. If this does not resolve to a valid state (i.e. a corresponding function in `FuncsSM` is present, or it exists in `FlowSM`) the state is set to empty and the SM will not run.
* **`next`** [str]: If advance is true and next specifies a valid state (checked like above) it is set as current


# Overhaul

## Changes from current code
* UIStateAdvance -> advanceStateSM
* setUIStateFlow -> setFlowSM
* UIRunStateMachine -> runSM
* UIStateLockout -> RunningSM (with reverse true/false)
* getUIStateIndexFromName -> getFlowIndexSM
* getUIStateNameFromIndex -> getFlowNameSM
* doneUIStateMachine -> isFinishedSM
* isUIState -> dropped
* isOrAfterUIState -> isOrAfterFlowSM

## Additional Info
* `persistSM`: is created in this module and registered with `regPersistentData("persistSM")` (core).
* The overrule mechanism for forcing to run the SM will not be implemented. It was never necessary and it contradicts the concept of a state machine.

## Test harness
`statemachine_test.lua`: a flow of dummy states recording their calls; cases: default order, jump by return value, `"wait"`/`"end"`/`"back"`, speed rule (0/1/true), `onload` with a saved record, exceptions (hold, goback), flags across `resetSM`, a custom `FlowSM`/`FuncsSM` joined (after/before/replace/merge, string ids), lockout while running, unlock after 3 s. Run via Execute, PASS/FAIL per case.

## Open
* *(decide)* precedence when both `nextSM` and the return value set a next state.
* *(decide)* exception display: dialog for errors, chat for notes?
* `next` parameter: Maybe it would be better to use false for the SM is finished (now -1) and use -1 for going back to the previous step?
* Trigger for SM: Is it necessary to give the trigger to a state? This cannot be done automatically as it always called with runSM. Regardless if provided with a new parameter or different wrapper functions it is additional complexity and should be worth it. So far this requirement never occured and I would tend to not implement it.
