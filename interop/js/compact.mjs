// Independent implementation of the optional L1 tuple mapping. This fixture
// verifier covers finite JavaScript-representable numbers; Python's wider exact
// Decimal profile is not asserted to be universally supported by JavaScript.
import fs from "node:fs";

const fields = {
  packet: ["id", "pragmatics", "atoms", "context", "permissions", "output", "evidence", "relations", "confidence", "carrier", "audit", "extensions"],
  pragmatics: ["type", "speech_act", "goal", "modifiers", "register", "urgency", "extensions"],
  atom: ["id", "kind", "value", "role", "datatype", "language", "attributes", "extensions"],
  relation: ["type", "arguments", "id", "confidence", "attributes", "extensions"],
  context: ["thread_id", "bindings", "references", "packet_id", "parent_packet_id", "conversation_id", "turn", "speaker", "audience", "time", "timezone", "window", "location", "extensions"],
  reference: ["packet_id", "depth", "agent", "label", "extensions"],
  permissions: ["mode", "scope", "forbid", "require_confirmation", "require_review", "require_logging", "limits", "extensions"],
  evidence: ["id", "source_type", "source_ref", "input_hash", "span", "supports", "description", "confidence", "extensions"],
  output: ["format", "schema", "channel", "target", "language", "max_bytes", "requirements", "extensions"],
};
const required = { packet: 6, pragmatics: 1, atom: 2, relation: 2, context: 1, reference: 1, permissions: 0, evidence: 2, output: 1 };
const defaults = {
  packet: { evidence: [], relations: [], confidence: 1, carrier: {}, audit: {} },
  context: { references: [] },
};
const children = {
  "packet.pragmatics": ["pragmatics", false], "packet.atoms": ["atom", true],
  "packet.relations": ["relation", true], "packet.context": ["context", false],
  "packet.permissions": ["permissions", false], "packet.evidence": ["evidence", true],
  "packet.output": ["output", false], "context.references": ["reference", true],
};

function unpack(tuple, shape) {
  if (!Array.isArray(tuple) || tuple.length < required[shape] || tuple.length > fields[shape].length) {
    throw new Error("invalid L1 tuple shape");
  }
  const result = structuredClone(defaults[shape] ?? {});
  tuple.forEach((value, index) => {
    if (value === null && index >= required[shape]) return;
    const key = fields[shape][index];
    const child = children[`${shape}.${key}`];
    if (child) {
      const [name, many] = child;
      if (many && !Array.isArray(value)) throw new Error("L1 collection must be array");
      result[key] = many ? value.map(item => unpack(item, name)) : unpack(value, name);
    } else result[key] = value;
  });
  return result;
}

function pack(value, shape, encode) {
  const tuple = fields[shape].map(key => value[key] ?? defaults[shape]?.[key] ?? null);
  while (tuple.length > required[shape]) {
    const key = fields[shape][tuple.length - 1];
    if (encode(tuple.at(-1)) !== encode(defaults[shape]?.[key] ?? null)) break;
    tuple.pop();
  }
  return tuple.map((item, index) => {
    const child = children[`${shape}.${fields[shape][index]}`];
    if (!child || item === null) return item;
    const [name, many] = child;
    return many ? item.map(value => pack(value, name, encode)) : pack(item, name, encode);
  });
}

export function verifyCompactVectors(file, validatePacket, encode, assert) {
  const fixture = JSON.parse(fs.readFileSync(file, "utf8"));
  for (const { compact, canonical } of fixture.positive) {
    assert(compact[0] === "L1" && compact.length === 2, "invalid fixture profile");
    const restored = { ...unpack(compact[1], "packet"), version: "0.1" };
    validatePacket(restored);
    assert(encode(restored) === encode(canonical), "L1 changed canonical semantics");
    assert(encode(["L1", pack(canonical, "packet", encode)]) === encode(compact), "L1 encode mismatch");
  }
  for (const compact of fixture.negative) {
    let rejected = false;
    try {
      if (compact[0] !== "L1" || compact.length !== 2) throw new Error("unknown L1 profile");
      validatePacket({ ...unpack(compact[1], "packet"), version: "0.1" });
    } catch { rejected = true; }
    assert(rejected, "negative L1 fixture accepted");
  }
  return { positive: fixture.positive.length, negative: fixture.negative.length };
}
