# Make the throttle window testable

The shared throttle gate (30 second sliding window, block-until after a 429) has bugs we only find in
production because we can't unit test it: the only way is to wait for real time to pass. Make the window and
block logic testable without waiting, without changing how it behaves today. Add tests for the window rollover
and for a block that has just expired.
