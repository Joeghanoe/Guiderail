# Stop reading status codes out of error messages

Several places decide what to do with a failed API call by checking whether the error message contains a
status such as ": 404" (the "no data yet" state of a customer). A message change or a translation breaks that
silently, and the check is repeated six times. Replace it with something that carries the status properly.
Behaviour must stay exactly the same for users.
