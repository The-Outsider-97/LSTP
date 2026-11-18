# Optional compact carrier for canonical v0.1

A sender and receiver explicitly select this carrier out of band. The default
interchange remains canonical v0.1 JSON. Existing canonical JSON and Lattice
entry points retain their formats. Unsupported peers receive canonical JSON.
No persisted packets require migration.

The standalone UTF-8 JSON array begins with the string L1. The remaining
positions, in order, are id, pragmatics, atoms, relations, context, confidence,
permissions, evidence, output, carrier and audit. All eleven positions are
mandatory and keep their canonical JSON values. A final object with exactly
one member named extensions carries the optional top-level extensions.
The canonical protocol version is 0.1. Array members inside every section keep
their original order. Apply ordinary canonical member, type, resource and
semantic checks to the expanded document. Reject unknown tags, wrong arity
and unrecognized members. No cascading alias substitution takes place.

A D1 delta has exactly three elements. After the tag come the lowercase hex
SHA-256 of the base packet's complete canonical UTF-8 bytes and an object
mapping zero-based decimal slot numbers (without leading zeros) to whole
replacement values. Omitted slots are inherited. Optional-slot presence cannot
change in a delta. Switch to L1 to add or remove that slot. An empty change
object carries the original packet. The default sender chooses a delta only
when its byte length is lower. A caller may supply a tokenizer-based cost
function. A decoded delta must pass all the same checks as a standalone frame.

The host retains the base under its authenticated session and policy scope.
After restart or out-of-order delivery, supply the exact authorized base or
request standalone retransmission. No ambient state or automatic network lookup
is permitted. Count the base transmission, acknowledgements and recovery in
any operational savings estimate. A digest identifies content and conveys no
authority. Reconstruct and validate the packet, then verify any host signature
over canonical bytes, evaluate host policy and apply replay checks as usual.

Python exposes compact_dumps and compact_loads. Compact frames have no signing
profile of their own. The read-only SLAI extraction view is a separate task
input and cannot be submitted to either packet decoder for execution.
