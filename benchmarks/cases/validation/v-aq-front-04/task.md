# The configure page is one 1000-line file

Nobody wants to touch the domain configuration screen any more: one file holds the page, the row virtualisation,
the move and impact selects, the bucketing and search functions and the environment detection. We want to add
bulk actions next sprint and need to be able to read it first.

Split it so each piece can be understood and tested alone. The screen must look and behave exactly as before.
No bulk actions yet.
