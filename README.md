# Liquor Cabinet #
**v0.0.1-alpha3**

*A desktop application to manage your personal booze inventory.*

Liquor Cabinet is currently in Alpha, and may break, or just plain not work.
It _shouldn't_ eat your data, but as usual there are no guarantees.

## Installing ##

### Windows ###
You will need to download the following dependencies before you'll be 
able to use Liquor Cabinet:

*   [Python 2.7](http://python.org/ftp/python/2.7.1/python-2.7.1.msi)
*   [PyQt4](http://www.riverbankcomputing.co.uk/static/Downloads/PyQt4/PyQt-Py2.7-gpl-4.8.1-1.exe)

A proper installer will be a goal for beta.

### Linux ###
Long story short, you should already have Python, and only need PyQt4, 
which should be in your distribution's repositories.

### Mac ###
I dont have any Macs available to test, so you're encouraged to give it the ol' college try.
You should only need PyQt4 which might be in Fink or Macports or 
whatever package manager it is you Mac people use.

## Running ##
Windows users can double-click `liquor_cabinet.bat` to launch the program.
You might need to edit it (right click, edit) to adjust your python path.

Other users will need to run `python guiclient.py` from a terminal, preferably from within its directory.

You'll notice a window and an icon in your system tray.
Closing the window will simply hide it, clicking the icon in your system tray will re-show the window.
Right clicking the icon will show a menu with which you can do most things with the program.

Your data is saved in `database.py` when you exit the program, and every few minutes while it runs.
If you're worried about new versions eating your data, make a backup regularly.

## Contributing ##
If you'd like to contribute to the project, send an email to [C Nelson](https://github.com/cnelsonsic)
and we'll think of something for you to do.

The #1 thing right now is making the GUI more featureful, specifically 
with respect to the predictive parts of the application.

The #2 thing is adding useful default data. 
This is mostly in the form of popular products and product information.

If you still have no ideas for things to do, there are several "TODO"s 
that would be nice to have completed.

## Copyright ##
    Liquor Cabinet Copyright (C)  2010  C Nelson
    This program comes with ABSOLUTELY NO WARRANTY; for details see the LICENSE file.
    This is free software, and you are welcome to redistribute it
    under certain conditions; see the LICENSE file for details.

