# Core

The core module has essential helper functions often used in other modules, but may be helpful on their own.

This and many other modules are designed to allow addons to be loaded into the game (e.g. additional card decks or a whole new expansion). Addons can have their own code and can integrate into the core code without the need to change it (e.g. new states for the SM, additional steps in a setup procedure, or even a completely different setup procedure). For more info see [**`addons`**](addons.md).

This is a module of the "Rubberduck TTS Framework" with basic functions, so all other modules of the framework depend on.

## Member Variables
| Variable | Description | Type
|---|---|---|
| [`boardsRTF={}`](#Places) | A table of base objects for placesRTF, mostly boardsRTF or mats with snap points. Those may have multiple states. | [tab]
| [`onSaveLoadFuncsRTF={}`](#onSaveLoadFuncsRTF) | A table holding functions to be all run upon game save and load. | [func{}]
| [`PersistentDataRTF={}`](#PersistentDataRTF) [tab] | A table to store persistent data in (survives save and load). | [tab]
| [`placesRTF={}`](#Places) | A table of keyed items, where the key is the place and the value specifies a snap point, a container, or a zone. | [tab]
| [`prefsRTF`](#prefsRTF) | A table holding the user settings for the framework | [tab]

### prefsRTF<a name="prefsRTF"></a>
This allows to set user default values and other settings for the whole framework. In the function summary tables you can see if a function supports the settings or not (Y=Yes, -=No, {params}=Only the stated params are supported). You can use this for your own purposes, just make sure to use a unique key as second level (where the function name is).

For framework functions the path is always like this: `prefsRTF.<function name>.<parameter name> = ...`

It is strongly recommended to use `setPref` and `getPref` to set and get the values (e.g. it avoids the "attempt to index a nix value" error for non-existing keys). Use `setPref` with a value of `nil` to delete a preference. Also see [`argsRTF`](#argsRTF) if you want to use the parameter normalization with honoring preferences for your own functions.

```lua
setPref("getSnapPos.relative", true)
--prefsRTF.getSnapPos.relative = true  would cause an error as getSnapPos is not defined
```

## Function Summary
| Function | Description | Return | prefsRTF
|---|---|---|---|
| [`getPersist`](#getPersist) | Retrieves persistent data from `PersistentData` with [`getTable`](#getTable). | [tab] | -
| [`getPref(path [str/tab])`](#prefsRTF) | Gets a preference with the specified path (either e.g. "opts.players.white", or {"opt", "players", "white"}).
| [`getTable`](#getTable) | This function gets a value of a key-value table regardless on which nested level. This is an alternative to a[k1][k2], or a.k1.k2, but avoids an error if any nest key is nil. | [tab] | -
| [`onSaveLoadFuncsRTF={order={persistent=0}, persistent=func(event [str])}`](#onSaveLoadFuncsRTF) | A table holding functions to be all run upon game save and load. Add your own functions if you need to run code then. | [func{}] | -
| [`regPersistentData(varname [str])`](#addPersistentKey) | Register a variable to be persistent over saving and loading (otherwise the value is lost). | - | -
| [`setPersist`](#setPersist) | Retrieves persistent data from `Opts` with [`setTable`](#setTable). | [tab] | -
| [`setPref(path [str/tab], value [any])`](#prefsRTF) | Sets a preference with the specified path (either e.g. "opts.players.white", or {"opt", "players", "white"}). For built-in functions the first level is the function name, the second the key. For your own purpose use a unique first level key. To **delete** a preference specify the value as `nil`.
| [`setTable(tgt [any{}], src [any/any{}], keys [str{}], insert [bool/num])`](#setTable) | Sets a value into a key-value table regardless on which nested level with different options how the value(s) are joined with existing values for flat lists. | [tab] | -

### onSaveLoadFuncsRTF<a name="onSaveLoadFuncsRTF"></a>
Upon game save and load (TTS functions `onSave` and `onLoad`) all functions in it are run (e.g. `persistent`, which saves persistent data) in the specified order. This way other modules can add code, which needs to run upon save or load. You can add your own code/function too (without overwriting other functionality).

#### Details
* **`.<function name> = function(event) ... end`**: 
* **`.order.<function name> = order`**: Specifies the order to run the functions. The key is the function name and the value the order.
  * Forbidden: Value **0** and values from **101 to 200** are reserved for the framework. Do **NOT** use one of those!
  * On Load: The functions are executed as defined by order from low to high; [`persistent`](#addPersistentKey) is always first (0).
  * On Save: The functions are executed in **reverse** order from high to low; [`persistent`](#addPersistentKey) is always last (ensuring that persistent data changed by other onSaveLoad functions is also saved).
  * You do not have to specify an order for your functions, they are still run (at the end on load, at the beginning on save).

#### Parameter for each Function
* **`event`**: Each function must accept one string parameter, which is either "load" or "save" to run the specific code each event.

#### Example
```lua
onSaveLoadFuncsRTF.myFunction = function(event)
  if event="load" then
    --...
  else
    --...
  end
end
onSaveLoadFuncsRTF.order.myFunction = "10"
```

### setTable(...)<a name="setTable"></a>
Sets or joins one or multiple values into a table and returns the final table. This is rather a complex function (which lies in the nature of the complexity to join tables), but also powerful. The major concepts are:
* MULTI Assignment: You can assign multiple values to multiple keys (within the same table) at once.
* AUTOREPEAT: For MULTI assignment you do not have to specify a value for each key, as the last provided value will be repeated until all keys do have a value.

#### Parameters
* **`tgt`** [tab]: The table to be changed (is changed as it is given as reference)
* **`src`** [any]: The value to be set into the table. Use value "nil" (with insert=nil) to remove a nested table. Use "{}" to create an empty nested table. The default behavior is that existing keys are replaced with val, new keys are created and val is assigned. This can be changed with "insert"
* **`src{}`** [any{}]: MULTI assignment: If you provide multiple values as flat table (no key-val), you can set values to multiple keys at once. The last key in "keys" MUST be a table (see examples "g"). All those keys are getting assigned the corresponding value form the "val" table. AUTOREPEAT: If there are less values than keys, the last value will be assigned to the remaining keys (see examples "f" and "h"), except if insert=4 or 6. Note: val={1}/key={"a","b","c"} will fill {"a","b","c"} with {1,1,1}, but if val={nil,1}, then it will fill with {nil,1,1}
* **`keys`** [str{}]: Any number of keys (at least 1) as table, where each subsequent key defines a nested table of the key before. NOTE: If you pass keys as variable it is overwritten by the function. To prevent this pass a copy (see table.copy).
* **`keys`** [str]: Alternatively to a key list you can specify a key path as string, e.g. "opts.players.white".
* **`keys=nil`**: If keys is nil then var must be a flat array (no key=val pairs, just values). val will be inserted as specified by insert.
* **`insert`** [bool/num]: How to insert val in var.
    * 0/nil: Add/Replace: Add new values, replace existing. Use this to remove a key completely (e.g. {var, nil, {"a", "b"}} to remove key "b" in sub-table "a")
    * 1/true: Join: The values from val (flat table) are inserted into the existing table (see example 1d), or a new table is created, i.e. the result is always a table (for the last key), regardless if val is a table or not:
        * If the last key does not exist, then a new table(!) is created and then the new values are inserted into this (see example 1c).
        * If the existing value is not a table it is converted to a table and then the new values are inserted.
        * If val is not a table it is just inserted, if it is a table, all items from the table are inserted (both are joined, but may have double entries).
    * 2:  Join Unique: Like 1, but values are not inserted if val already present, nor replaced if key is already present (no double entries).
    * 3:  Join strict: Like 1, but "val" is inserted into the table of the last key as is, i.e. if val is a table the values are not joined, but the val-table is inserted as sub-table. See example 3. However, the result is also always a table (for the last key). If val is nil the key will be removed. If the key to which val should be assigned is not a table, it is converted to a table and then val is inserted as is (see example 3a and 3b).
    * 4:  Replace: Existing values of the last key are removed, "val" is inserted instead (if nil the entry will be removed (this is different to insert=nil), i.e. AUTOREPEAT does not work). See example 4. Otherwise it is like 0, e.g. if the last key is not a table, val is inserted as is.
    * 5:  Remove: val (value or table of values) is removed from table of the last key (of if not a table then the key is removed if current value = val). If val=nil then nothing is removed (use insert=4)! See example 5. If all elements are removed from a sub-table then an empty sub-table is returned (not nil), so use #sub-table==0 to check if it is empty. See example 5m.
    * 6:  Add/Replace, but not if nil (w/o AUTOREPEAT): Like nil (overwrites existing values), but without AUTOREPEAT, i.e. does not update existing items if val is nil (therefore you can update multiple values (MULTI assign), but still avoid to overwrite existing values if new one are not set (=nil)).
    * 7:  Add only (do not overwrite): Like insert=nil, but does not update existing items (AUTOREPEAT is supported, i.e. setTable({a=false}, {true, nil}, {{"a", "b"}}, 7) results in {a=false, b=true})

#### Examples
Examples are grouped with the number of the insert mode. Examples with the same letter use the same input data, but different modes.
```
* Ex 0: Insert=0/nil: Add/Replace
    * 0a: setTable({b=1, d=7}, 2, "b")  --->  result: a={b=2, d=7}
    * 0b: setTable({b=1, d=7}, {2}, "b")  --->  result: a={b={2}, d=7}
    * 0c: setTable({b=1, d=7}, 2, "c")  --->  result: a={b=1, c=2, d=7}
    * 0e: setTable({b={c=1, d=3}}, 5, {"b", "e", "f"})  --->  result: a={b={c=1, d=3, e={f=5}}}
    * 0f: setTable({b={c=1, d=3}}, {5, 6, 7}, {"b", "e", {"f", "g", "h"}})  --->  result: a={b={c=1, d=3, e={f=5, g=6, h=7}}}
    * 0g: setTable({b={c=1, d=3}}, {5, 6}, {"b", "e", {"f", "g", "h"}})  --->  result: a={b={c=1, d=3, e={f=5, g=6, h=6}}}
    * 0h: setTable({b={c=1, d=3, e={f=4, h=6}}}, {nil, 8, nil}, {"b", "e", {"f", "g", "h"}})  --->  result: a={b={c=1, d=3, e={g=8, h=8}}}
* Ex 1: Insert=1/true: Join
    * 1a: setTable({b=1, d=7}, 1, "b", 1)  --->  result: a={b={1, 1}, d=7}
    * 1b: setTable({b=1, d=7}, {1}, "b", 1)  --->  result: a={b={1, 1}, d=7}
    * 1c: setTable({b=1, d=7}, 1, "c", 1)  --->  result: a={b=1, c={1}, d=7} -- same result if val={1} (instead of 1)
    * 1h: setTable({b={c=1, d=3, e={f=4, h=6}}}, {7, 8, nil}, {"b", "e", {"f", "g", "h"}}, 1)  --->  result: a={b={c=1, d=3, e={f={4, 7}, g={8}, h={6, 8}}}}
    * 1i: setTable({b={c=1, d=3, e={1}}}, {1, 5, 6, 7}, {"b", "e"}, true)  --->  result: a={b={c=1, d=3, e={1, 1, 5, 6, 7}}}
    * 1j: setTable(nil, {{g=1, h=2}}, {"b", "c"}, 1)  --->  result: a={b={c={{g=1, h=2}}}}  --->  setTable(a, {{g=8, h=9}}, {"b", "c"}, 1), result: a={b={c={1={g=1, h=2}, 2={g=9, h=8}}}}
* Ex 2: Insert=2: Join Unique
    * 2a:to 2c same as 1a to 1c
    * 1h: setTable({b={c=1, d=3, e={f=4, h=6}}}, {7, 8, nil}, {"b", "e", {"f", "g", "h"}}, 2)  --->  result: a={b={c=1, d=3, e={f={4, 7}, g={8}, h={6, 8}}}}
    * 2i: setTable({b={c=1, d=3, e={1}}}, {1, 5, 6, 7}, {"b", "e"}, 2)  --->  result: a={b={c=1, d=3, e={1, 5, 6, 7}}}
* Ex 3: Insert=3: Join strict
    * 3a: setTable({b=1, d=7}, 2, "b", 3)  --->  result: a={b={1, 2}, d=7}
    * 3b: setTable({b=1, d=7}, {2}, "b", 3)  --->  result: a={b={1, {2}}, d=7}
    * 3c: setTable({b=1, d=7}, 2, "c", 3)  --->  result: a={b=1, c=2, d=7}
    * 3d: setTable({b=1, d=7}, {2}, "c", 3)  --->  result: a={b=1, c={2}, d=7}
    * 3h: setTable({b={c=1, d=3, e={f=4, h=6}}}, {7, 8, nil}, {"b", "e", {"f", "g", "h"}}, 3)  --->  result: a={b={c=1, d=3, e={f={4, 7}, g=8, h={6, 8}}}}
    * 3j: setTable({b={c=1, d=3, e={1}}}, {5, 6}, {"b", "e"}, 3)  --->  result: a={b={c=1, d=3, e={1, {5, 6}}}}
    * 3k: setTable({b={c=1, d=3, e={1}}}, {5, 6}, {"b", "f"}, 3)  --->  result: a={b={c=1, d=3, e={1}, f={5, 6}}}
* Ex 4: Insert=4: Replace
    * 4a: setTable({b=1, d=7}, 2, "b", 4)  --->  result: a={b=2, d=7}
    * 4b: setTable({b=1, d=7}, {2}, "b", 4)  --->  result: a={b={2}, d=7}
    * 4c: setTable({b=1, d=7}, 2, "c", 4)  --->  result: a={b=1, c=2, d=7}
    * 4d: setTable({b=1, d=7}, {2}, "c", 4)  --->  result: a={b=1, c={2}, d=7}
    * 4h: setTable({b={c=1, d=3, e={f=4, h=6}}}, {nil, 8, nil}, {"b", "e", {"f", "g", "h"}}, 4)  --->  result: a={b={c=1, d=3, e={g=8}}}
    * 4j: setTable({b={c=1, d=3, e={1}}}, {5, 6}, {"b", "e"}, 4)  --->  result: a={b={c=1, d=3, e={5, 6}}}
* Ex 5: Insert=5: Remove
    * 5a: setTable({b=1, d=7}, 2, "b", 5)  --->  result: a={d=7}
    * 5b: setTable({b=1, d=7}, 2, "c", 5)  --->  result: a={b=1, d=7}
    * 5h: setTable({b={c=1, d=3, e={f=4, h=6}}}, {4, 8, nil}, {"b", "e", {"f", "g", "h"}}, 5)  --->  result: a={b={c=1, d=3, e={h=6}}}
    * 5l: setTable({b={c=1, d=3, e={1, 5, 6, 7}}}, {5, 6, 7}, {"b", "e"}, 5)  --->  result: a={b={c=1, d=3, e={1}}}
    * 5m: setTable({b={c=1, d=3, e={1, 5, 6, 7}}}, {1, 5, 6, 7}, {"b", "e"}, 5)  --->  result: a={b={c=1, d=3, e={}}}
* Ex 6: Insert=6: Add/Replace, but not if nil:
    * 6h: setTable({b={c=1, d=3, e={f=4, h=6}}}, {nil, 8, nil}, {"b", "e", {"f", "g", "h"}})  --->  result: a={b={c=1, d=3, e={f=4, g=8, h=6}}}
* Ex 7: Insert=7: Add/Replace, but do not overwrite:
    * 7h: setTable({b={c=1, d=3, e={f=4, h=6}}}, {nil, 8, nil}, {"b", "e", {"f", "g", "h", "i"}})  --->  result: a={b={c=1, d=3, e={f=4, g=8, h=6, i=8}}}
```


# Internal

## Member Variables
| Variable | Description | Type
|---|---|---|
| [`PersistentDataVarsRTF={"PersistentDataRTF"}`](#PersistentDataRTF) | A table with the names of all variables which should be persistent data. Therefore all variables to be stored persistently must have different names. | table

## Function Summary
| Function | Description | Return | prefsRTF
|---|---|---|---|
| [`argsRTF(params [tab], specs [tab], noset [bool/tab], name [str])`](#argsRTF) | A helper function used by most functions to normalize the given parameters as table with honoring `prefsRTF`. | [tab] | -
| `onLoad` | This function is <a href="https://api.tabletopsimulator.com/events/#onload">called by TTS automatically</a>. It runs all `onSaveLoadFuncsRTF` with the parameter "load". | - | -
| `onSave` | This function is <a href="https://api.tabletopsimulator.com/events/#onsave">called by TTS automatically</a>. It runs all `onSaveLoadFuncsRTF` with the parameter "save". The return value of `persistent` is the hardcoded return value for `onSave`. | - | -
| [`onSaveLoadFuncsRTF.persistent`](#PersistentDataRTF) | Saves and loads the whole table `PersistentDataRTF` JSON encoded. | - | -

### argsRTF(...)<a name="argsRTF"></a>
The parameters are normalized to become a keyed table with defaults and `prefsRTF` applied. Used by most frameworkd functions.

It allows the caller of a function to supply the parameters in differnt ways and all are converted into a table. When calling argsRTF the function provides keys to get a keyed table (note: it is also possible to not provide keyes to get a flat list, but then no default values can be assigned by argsRTF; not recommended):
* A single parameter of any type
* A flat list of parameters, which must then be specified in the correct order
* A keyed table of parameters

The value of a paramter is determined by: provided value >>> `prefsRTF.<name>.<param-key>` >>> default value in specs >>> `nil`

#### Parameters
* **`params`** [any/tab]: The parameter for the function as single parameter of any type, or as keyless list, or as keyed table.
* **`specs`** [tab]: Holds two things:
  * The keys for the parameters as flat list (in the order they should be provided)
  * The default values as keyed items
* **`settings=true`** [bool/tab]: If `false` values in `prefsRTF` are ignored, thus preventing this functionality. Instead of true/false a table can be provided with the keys of the parameters, which are supported (settings for unlisted keys are ignored).
* **`name`** [str]: The function name to get the values from `prefsRTF`, thus only needs to be set if noset is not `true`. (Note: Unfortunately there is no way to get the name of the current function, so it is necessary to provide it.)

#### Example
```lua
setPref{"getSnapPos.offset", {x=2}}
getSnapPos{1, "763234"}
function getSnapPos(p)
  p = argsRTF(p, {"sid", "obj", "relative", "offset", obj=Global, relative=false}, "getSnapPos", {"obj"})
  -- p = {sid=1, obj="763234", relative=false, offset={x=2}}
    -- getSnapPos{sid=1, obj="763234"} would result in the same
    -- getSnapPos(1) would result in p = {sid=1, obj=Global, relative=false, offset={x=2}}
```

### PersistentDataRTF<a name="PersistentDataRTF"></a>

#### onSaveLoadFuncsRTF.persistent
TTS does not save variables by default. The function `onSaveLoadFuncsRTF.persistent` combines all variables in `PersistentDataVarsRTF` to one table (value is also key, e.g. ["PersistentDataRTF"]=PersistentDataRTF), JSON encodes it and returns it. `onSave` uses this return values as its hardcoded return value. `onLoad` does the reverse and restores all variables.

#### PersistentDataRTF
The table `PersistentDataRTF` is provided by default to store persistent data. It does not have data by default. For different purposes it is recommended to use separate sub-keys (e.g. `PersistentDataRTF.MyPlayers` for player related data). 

#### regPersistentData(...)<a name="addPersistentKey"></a>
`PersistentDataRTF` is provided by default. For different purposes (or already existing code) you may want to make other variables also persistent. Use this function to register additional variables, which should be saved and loaded automatically. Some modules (e.g. **dialog**, **statemachine**) also use this with their own permanent variables, so you might want to check not to use one of those.

##### Parameters
* **`varname [str]`**: The name of the variable to be stored persistently.

##### Example
```lua
MyOwnPermanent = {}
regPersistentData("MyOwnPermanent")
```

# Overhaul

* getPref/setPref are another wrapper (like the old setData/getData, which will still exist for module dialog, but renamed) and calls get/setTable with "prefsRTF" as first key and insert=4.
* Can metatable functions be used for setTable and other table helper functions we have?

## Exceptions

Should go into core maybe (would also fit with popups then).

## Popup dialogs

Popups can be usefule even without big dialogs for which the module dialog is meant for, however it may share a lot of code. So the question is to include this here or in module dialog.

The idea is basically that of today's UIInfoBox with an added feature. A timed popup can be placed in the center as today. But a rolling variant for multiple popups should be added. The code in "Reference Code" was taken from another TTS mod which implements this functionality. The dialogs are placed in the lower right corner of the screen. Additional popups stack on top of it. After the time (set for each popup) they disappear and the popups above "fall down" to fill the gap. Right now the popups fade in, i.e. slowly move in from the side. But when disappearing they disappear immediatey. If possible they should also fade out, i.e. slowly move to the right out of the screen. The screen side right or left should be configurable.

### Reference Code
```lua
function Sidepopup_Init()
    local xmlglobal = UI.getXmlTable()
    if xmlglobal==nil then xmlglobal = {} end
    local xmlself = self.UI.getXmlTable()
    local globalassets = UI.getCustomAssets()
    local selfassets = self.UI.getCustomAssets()

    local function table_copy(obj, num, seen)
        if type(obj) ~= 'table' then return obj end
        if seen and seen[obj] then return seen[obj] end
        local s = seen or {}
        local res = setmetatable({}, getmetatable(obj))
        s[obj] = res
        for k, v in pairs(obj) do
            local kk = table_copy(k, num, s)
            if kk=="id" then
                res[kk] = table_copy(v, num, s)..num
            else
                res[kk] = table_copy(v, num, s)
            end
        end
        return res
    end

    local function doit()
        local isglobal = false
        for _, x in ipairs(xmlglobal) do
            if x.attributes.id==sidepopuppanel then
                isglobal = true
                break
            end
        end
        if not isglobal then
            for _, x in ipairs(xmlself) do
                if x.attributes.id==sidepopuppanel then
                    for j = 1, maxsidepopups do
                        xmlglobal[#xmlglobal+1] = table_copy(x, j)
                        xmlglobal[#xmlglobal].attributes.id = sidepopuppanel..j
                    end
                else
                    table.insert(xmlglobal, x)
                end
            end
            UI.setXmlTable(xmlglobal)
            --[[
            for _, x in ipairs(selfassets) do
                table.insert(globalassets, x)
            end
            UI.setCustomAssets(globalassets)
            --]]
        end
    end

    doit()
    --Wait.time(function() doit() end, 5)
end

-- Requires a global empty table sidepops = {}
-- param: txt, col1, pl1, col2, pl2
function Sidepopup_message(params)
    --if UI.loading then return end
    local sidepopups = Sidepopup_getNext()

    local function doit()
        UI.setAttribute("sidepopup_color1"..sidepopups, "color", params.col1) 
        UI.setAttribute("sidepopup_color2"..sidepopups, "color", params.col2) 
        UI.setAttribute("sidepopup_player1"..sidepopups, "text", params.pl1) 
        UI.setAttribute("sidepopup_player2"..sidepopups, "text", params.pl2) 
        UI.setAttribute("sidepopup_value"..sidepopups, "text", params.txt)
        UI.setAttribute("sidepopup"..sidepopups, "offsetXY", "0 "..((sidepopups-1)*150))
        UI.show("sidepopup"..sidepopups)
        Wait.time(function() print("time") Sidepopup_remove() end, sidepopup_showtime)
    end

    if not sidepopups then
        Sidepopup_remove()
        Wait.time(function()
            sidepopups = Sidepopup_getNext()
            if sidepopups then doit() end
        end, 1)
    else
        doit()
    end
end

function Sidepopup_remove()
    --function doit()
        local sidepopups = Sidepopup_getNext()
        if sidepopups==1 then return end
        if not sidepopups then sidepopups = maxsidepopups + 1 end
        local removethis = "sidepopup"..(sidepopups-1)
        if sidepopups > 2 then
            --UI.setAttribute("sidepopup1", "active", true)
            --UI.show("sidepopup1")
            --UI.setAttribute("sidepopup"..sidepopups, "active", false)
            for i = 2, sidepopups-1 do
                UI.setAttribute("sidepopup_color1"..(i-1), "color", UI.getAttribute("sidepopup_color1"..i, "color"))
                UI.setAttribute("sidepopup_color2"..(i-1), "color", UI.getAttribute("sidepopup_color2"..i, "color"))
                UI.setAttribute("sidepopup_player1"..(i-1), "text", UI.getAttribute("sidepopup_player1"..i, "text"))
                UI.setAttribute("sidepopup_player2"..(i-1), "text", UI.getAttribute("sidepopup_player2"..i, "text"))
                UI.setAttribute("sidepopup_value"..(i-1), "text", UI.getAttribute("sidepopup_value"..i, "text"))
            end
            UI.setAttribute(removethis, "hideAnimation", "")
        else
            UI.setAttribute(removethis, "hideAnimation", "SlideOut_Right")
        end
        UI.hide(removethis)
    --end

    --UI.hide("sidepopup1")
    --doit()
    --Wait.time(function() doit() end, 0.25)
end

function Sidepopups_removeAll()
    for i = 1, maxsidepopups do
        UI.setAttribute("sidepopup"..i, "active", "false")
    end
    local spn = Sidepopup_getNext()
    if not spn or spn>1 then
        timeRetrigger("sidepopups", function() Sidepopups_removeAll() end, 5)
    end
end

function Sidepopup_getNext()
    local i = 1
    while UI.getAttribute("sidepopup"..i, "active")=="true" do
        i = i + 1
        if i > maxsidepopups then return false end
    end
    return i
end
```