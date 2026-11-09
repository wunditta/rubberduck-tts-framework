# State Machine

The state machine (SM) is a generic flow control framework and is most usefule in cases where player inputs (e.g. dialogs) and scripted object manipulation intervene, which is typical for a setup procedure. The SM is implemented as a table of state functions (one function per state) and a default order (see SM Flow). A state does its work, then either the next state in the default order runs, or the state defines a different state to run next. In addition the trigger for the next state can be defined, i.e. immediately, waiting for a trigger (e.g. pushing a button, hotkey, dialog button), etc.

The SM is a "Rubberduck TTS Framework" module (`statemachine.lua`) and depends on the following other modules:
* "core.lua"

## Member Variables

| Variable | Description | Type
|---|---|---|
| [`smFuncs`](#smfunc) | A table of functions, one for each state (same name) | table{func}
| `smFlow` | A table of strings or tables, specifying the default order of the states | table{string|func}
| `smTexts` | A table with a subtables with texts to be shown before and after each state | table{table}

### smFuncs<a name="smfunc"></a>

```lua
smFlow = {"init", "setup"}
smFuncs = {
  ["init"] = function(ctx)
    ...
  end,
  ["setup"] = function(ctx)
    ...
  end
}
```

## Functions

* `smRun(trigger, speed)` — the only way to start the machine: by the Setup/Fast Setup buttons, hotkeys, a dialog's OK, the `custom` message of the file interface, and `onLoad` (for `onload` states). It refuses while a state is running or a dialog is open (today's lockout); the lock is cleared when the state returns or the dialog closes; a second press within 3 s on a locked machine unlocks and reruns (today's `UIStateForceRun`).
* After a state returns the machine resolves the next state (pending record from `smNext`/the return value, else `smFlow` order), writes the record, shows the state's `after` text on the button, and continues at once if the speed rule says so, otherwise stops. `speed` is kept for the whole run until the machine stops.
* `smState()` → current state name, `smPrev()`, `smIsOrAfter(name)` (today's `isOrAfterUIState`), `smDone()` resets the machine to the first state.

## Tables

* `smFuncs`: The state functions, one per state name: `smFuncs.setup = function(ctx) … end`.
* `smTexts` — the button texts and info texts per state (`prev` = while the state runs, `after` = when it waits afterwards; today's `UIStateTxt`), looked up by state name, joined the same way.

## Flow Control

Each state can define the next state. For a linear default flow it is easier to define the flow upfront.

No matter how the order is determined there is always only one state, which is the "current state":
* "Active state": If a state is running it is the running ("active") state.
* "Pending state": If no state is running it is the one which will be started next ("pending").
* Immediately after a state has finished the (new) "current state" is set, either it was specified in the finished state or the next one from the default flow will be taken.
* For the current state it is also defined if it should start automatically, on loading the game, etc. See "Default Flow" parameters for details.

In addition a speed can be set for the machine to run (`smSpeed`). This is a number or true (always), where 0 is default speed and a higher number means faster speed, i.e. some states are run automatically with default values instead of waiting for user input.

### Default Flow

```lua
smFlow = {{name="init", onload=true, restart=true}, {name="custom", restart=1}, "faction", {name="manual", restart=1}, "dialog", "setupboard", {name="mainboard", restart=true}, "cleanup"}
```

The default flow is specified in "smFlow", which is a list of the states in order. Each element is:
* "name": A string, which is the state name or id
* `{id="name", ...}`: A table with these parameters:
  * `id`: The state name. A plain string is the same as `{id="name"}`.
  * `onload=true`: After a game load the machine continues with the current state. Default is false: after a load the machine waits for a trigger.
  * `restart`: This defines if the MS should be run again after this state has finished, i.e. after the next state was set the machine is started and will run the next state immediately
    * `restart = true/false`: True will always continue, false will wait (default).
    * `restart = n`: The SM will be started automatically if the current speed is ≥ n, i.e. n is the **minimum** number "smSpeed" has to be to restart the SM automatically (in other words: the higher n is, the higher the speed needs to be to run it automatically).
  * `dialog="panelid"` (requires the "dialog" module): The state shows this dialog and waits (SM stops, keeps the current state, and waits for a trigger from one of the dialogs buttons). If "OK" the next state becomes the current and the SM is called (as normally something should happen after a dialog was confirmed). "Cancel" closes the dialog, stays with the current state and waits again). For simple cases no function in "smFuncs" is needed. However, a function can be defined and is called before the dialog is shown (so things happen in the background while the dialog is shown).
  * `workflow="phase" or true` (requires the "workflow" module): This depends on how the workflows are implemented. The value is forwarded to the workflow caller function. If only one workflow is defined then "true" will start it, otherwise the value defines which workflow to run. No "smFuncs" function will be called (even if present).
  * `text="key"`: The `smTexts` key if it differs from the state name.

### Special Flow

UINextState()

`nil` → the next state in `smFlow` (then `speed` decides whether it runs now or after a trigger); a state name → jump there (same `speed` rule); `"wait"` → stop here, the same state continues on the next trigger (today's "rerun the current state"); `"end"` → the machine is finished (today's `nextstate=-1`); `"back"` → the previous state.

* `smNext(name, opts)` is the function form of the return value for code that is not the state function itself (a dialog callback, a button of a state): `opts={run=true}` continues immediately, `opts={wait=true}` waits for a trigger. It sets the pending record; a later return value of the running state does not override it *(decide: or the other way round)*.

### Error Handling

addUIStateException()

## State Functions

* `smFuncs.<name>(ctx)`: Each function is an element of "smFuncs", named equal to the state name (see smFlow).
* `ctx` = `{state=<name>, speed=<n>, trigger=<what started this run>, prev=<previous state>}`.
* States run inside a coroutine started by the machine, so they may `wait`, move objects and use `waitdone`; the machine continues only when the function has returned.
* Return value decides what comes next (see smFlow > Special Flow).
* A state must not call `smRun` itself; it returns, the machine proceeds.

## Flags and exceptions

* Flags: `smFlag(name, value)` / `smFlag(name)` — booleans that survive a load (in the record), cleared by `smDone` (today's `setUIFlag`/`getUIFlag`, e.g. `cardmats`, `startdeck`, `qm_role`).
* Exceptions: `smException(kind, level, text)` — collected while a state runs, evaluated when it returns: `kind="hold"` → the machine waits for a trigger, whatever the speed (the players fix something), `kind="goback"` → the previous state runs again; `level="error"|"note"` decides the colour and whether the texts are shown in a dialog or only in the chat *(decide)*. The texts are shown through a callback the dialog module registers (`smRegisterShow(fn)`); the machine itself prints nothing. Today's `addUIStateException`, `getUIStateExceptions`, `removeUIStateExit`.

## Persistence

* One record in `Opts.sm` (core persistence): `{state=, prev=, pending=, pendingrun=, speed=, flags={}, onload=}` — written by the machine only, read on load; `onLoad` calls `smLoad()` which continues with the pending state if its entry says `onload=true`, else just restores the texts and waits.

## Custom sets

* A set's `smFlow`, `smFuncs` and `smTexts` are joined onto the core's by function "joinTree" (see docu in module "core") when the set is recognised (the "custom" state), before the dialog. `smFlow` elements are addressed by id; the string form joins as its own id (so `"faction"` twice adds nothing). A set introduces a new state by adding it to `smFlow` (`after=`/`before=`) with its function in `smFuncs`, and replaces a state by defining the same key in `smFuncs`.

## Test harness

`statemachine_test.lua`: a flow of dummy states recording their calls; cases: default order, jump by return value, `"wait"`/`"end"`/`"back"`, speed rule (0/1/true), `onload` with a saved record, exceptions (hold, goback), flags across `smDone`, a custom `smFlow`/`smFuncs` joined (after/before/replace/merge, string ids), lockout while running, unlock after 3 s. Run via Execute, PASS/FAIL per case.

## Open

* *(decide)* precedence when both `smNext` and the return value set a next state.
* *(decide)* exception display: dialog for errors, chat for notes?
* *(decide)* the names (`sm` prefix, `smFlow`, `smFuncs`).