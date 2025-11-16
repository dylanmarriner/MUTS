# Implementation Flows

1. SWAS disable -> per-gear torque overrides via ECU queue.
2. 1st/2nd boost-cut relief using safe torque deltas (+Nm only).
3. Valet mode enable/disable with PIN and torque/RPM caps.
4. ECU queue producer/consumer pattern with simulation + future J2534 transport.
5. Virtual dyno pull returning peak hp/torque (later: curves + plotting).
6. "Limit Finder" wizard over logs (future): identify the active limiter.
7. Hardware swap: abstract transport so simulation can be replaced with J2534 safely.
