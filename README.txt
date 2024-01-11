This tool assumes a locally installed database of MTG cards, which must contain at least names and color identities.
render_db_upload.py and routes.py are WIP documents for webapp version.
app.py contains some unnecessary functions currently being written for the webapp version.
I've left Jupyter in requirements as I use it for some testing, but it is not needed for any functionality.

This tool hooks into what seems to be a vestigial JSON endpoint at EDHREC. I found it from a comment on reddit 7 years ago.
Running a search for only colorless cards will work, but it takes a very long time to poll effectively every legendary creature on EDHREC.

Partner commanders are not yet implemented. (I forgot about them, oops.)

-- Running app.py in the command line starts the command line tool. --