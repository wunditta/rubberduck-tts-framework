# Rubberduck TTS Framework

This framework (short RTF) is a comprehensive collection of sophisticated functions for different purposes. They are divided into different modules you can insert into your code as needed. Each module states other required modules at the beginning with a remark line `-- include "module"`.

If you are using <a href="https://www.sublimetext.com">Sublime Text</a> you may want to install the package <a href="https://github.com/wunditta/tabletop-simulator-editor">Tabletop Simulator Editor package</a>, which has an "include" function built into it. Note: TTS does not support includes or required, so the function is simulated by automatically injecting the code of the included files into the main file upon uploading to TTS. However, this is done very conveniently and secure (you can even edit the whole code file and separate it later).

## Overview
The following modules are included:

| Module | Purpose
|---|---|
| [**core**](core.md) | Basic functions used by all other modules, e.g. `...`
| [**statemachine**](statemachine.md) | Enables to run smaller code packages (states) and wait between each of them until the players trigger the next. Typical examples are interactive setup procedures (table is prepared, a dialog is shown, further things are prepared depending on the dialog choices), or different phases within a player turn.
| [**dialog**](dialog.md) | The basic function is to automatically collect the dialog choices in a table. I also allows for more graphical dialogs, i.e. replacing a checkbox, radio buttons, multi-state buttons with images in a quite easy way. Furthermore it is possible to create dynamically generated dialogs where parts of are hidden depending on other selections.

## Basic Concepts

* **Internal**: The documentation of each module is split in two major parts, the normal documentation for coding with it and an "Internal" part for the internal working mechanisms and functions, which normally are not needed. Also, some things are marked with "internal:" in the normal part, which follow the same idea.
* **Preferences**: There is a generic mechanism to define user presets for many functions, i.e. you may define the defaults for any of their parameters. See `setPref` in [**`core`**](core.md) for details. Those are not mentioned explicitely. Only special preferences outside this scheme are.

## Hello World! (sort of)
Based on LE Aliengi