# Dialog

Several features facilitate the usage of dialogs, especially graphical ones:
* Automatically stores each selected option of a dialog in a table
* Use button images for toggle buttons (on/off), radio buttons (only one of several can be active), etc (the trick: certain prefixes to the id of an element defines its behavior)
* Define dependencies (one selection also de/selects others) or blockers (prevent certain combinations) which are checked while the dialog is running
* Show certain parts of a dialog only under certain conditions, i.e. a dynamically built dialog

This and many other modules are designed to allow addons to be loaded into the game (e.g. additional card decks or a whole new expansion). Addons can have their own code and can integrate into the core code without the need to change it (e.g. new states for the SM, additional steps in a setup procedure, or even a completely different setup procedure). For more info see [**`addons`**](addons.md).

This is a module of the "Rubberduck TTS Framework" and depends on these other modules: [**`core`**](core.md)