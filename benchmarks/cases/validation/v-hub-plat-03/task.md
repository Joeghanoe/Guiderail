One of our connectors needs more delivery attempts before a message is dead-lettered: 5 instead of 3, for its own
queue only. Today every connector says 3. Make that possible and set it to 5 for that one connector (use the first
one listed). Other connectors must keep 3 and need no change.

Make sure the connector and the queue agree. Report which files you changed and how you checked.
