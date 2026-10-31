# Show when the health picture is incomplete

The backend now tells us, per snapshot, whether the data behind it is complete, partial or failed
(`dataQuality` in the snapshot response). Today the portal ignores it, so when an input source is down the fish
look healthy and an operator reads that as good news.

Make the health page show the operator when the picture is partial or failed. Complete should look exactly as
it does now. Customers see the same view; they should not get operator-only wording.
