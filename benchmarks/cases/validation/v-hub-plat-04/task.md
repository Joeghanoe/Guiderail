Last week the nightly bulk download for one of our connectors silently did not run for three days and nobody
noticed. We have an alert when a download fails, but it did not fire because nothing ran at all.

Add monitoring so we find out when it does not complete. Keep the change to what is needed; the failure alert stays.
Tell me how you checked the query and what I need to run to deploy it.
