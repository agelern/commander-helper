**Apr 03, 2024**  
  Worked a lot offline in spare minutes here and there. My original intent with the project was to showcase my assorted data skills with things like AWS services and general data warehousing. As I continued tinkering, it became obvious that there was a much simpler implementation that did less showcasing but was a far better end-product. THEREFORE, I've begun creating a second version that is totally serverless and simply handles 2 APIs, performing transformations in between. This will likely be what feeds the webapp version which I'll be "finishing" "soon."
  
Also, partner-type commanders are mostly implemented now. Doctors and backgrounds are next.

**First Commit**  
This tool assumes a locally installed database of MTG cards, which must contain at least names and color identities.
render_db_upload.py and routes.py are WIP documents for webapp version.
app.py contains some unnecessary functions currently being written for the webapp version.
I've left Jupyter in requirements as I use it for some testing, but it is not needed for any functionality.

This tool hooks into what seems to be a vestigial JSON endpoint at EDHREC. I found it on an ancient reddit comment. If anyone knows more about this, I'd love to hear about it.
Running a search for only colorless cards will work, but it takes a very long time to poll effectively every legendary creature on EDHREC.

Partner commanders are not yet implemented.
