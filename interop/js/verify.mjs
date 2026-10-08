// Independent dependency-free LSTP v0.1 conformance verifier.
//
// This implementation deliberately does not import, spawn, or invoke the Python
// package. It consumes the same versioned manifest as the Python conformance
// harness and independently checks the frozen JSON and canonical-Lattice surface.

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..");
const CONF = path.join(ROOT, "conformance", "v0.1");
const MANIFEST = JSON.parse(
  fs.readFileSync(path.join(CONF, "manifest.json"), "utf8"),
);

const BIDI = /[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/u;
const REQUIRED_TOP = [
  "id",
  "version",
  "pragmatics",
  "atoms",
  "relations",
  "context",
  "confidence",
  "permissions",
  "evidence",
  "output",
  "carrier",
  "audit",
];
const TOP_ALLOWED = new Set([...REQUIRED_TOP, "extensions"]);
const PERMISSION_ALLOWED = new Set([
  "mode",
  "scope",
  "forbid",
  "require_confirmation",
  "require_review",
  "require_logging",
  "limits",
  "extensions",
]);
const MODES = new Set(["RO", "SUGGEST", "PREVIEW", "RW", "EXEC", "COMMIT"]);
const SIDE_EFFECT_MODES = new Set(["RW", "EXEC", "COMMIT"]);
const SPECIAL_ARGUMENTS = new Set(["SELF", "NOW", "USER", "SYSTEM"]);
const CORE_RELATIONS = new Set([
  "is",
  "has",
  "part_of",
  "located_at",
  "causes",
  "requires",
  "references",
  "produces",
  "requests",
  "answers",
  "outcome.success",
  "outcome.failure",
  "outcome.partial",
  "outcome.refused",
  "outcome.unsupported",
  "outcome.needs_confirmation",
  "outcome.needs_context",
]);
const OCTAD_SEGMENTS = ["π", "A", "R", "C", "κ", "Π", "E", "Ω"];
const ATOM_KINDS = new Set(["entity", "concept", "value", "event", "time", "location", "resource", "proposition", "unknown"]);
const EVIDENCE_TYPES = new Set(["user", "sensor", "model", "tool", "retrieved", "inferred"]);
const OUTPUT_FORMATS = new Set(["NL", "LATTICE", "JSON", "YAML", "TABLE", "CODE", "FILE", "NONE"]);
const ATOM_ID = /^a(?:0|[1-9][0-9]*)$/u;
const RELATION_ID = /^r(?:0|[1-9][0-9]*)$/u;
const EVIDENCE_ID = /^e(?:0|[1-9][0-9]*)$/u;
const QUALIFIED = /^[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)*$/u;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function record(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
function scopedString(value, label) {
  assert(typeof value === "string" && value.length > 0, `invalid ${label}`);
}
function identifier(value, label) {
  assert(typeof value === "string" && QUALIFIED.test(value), `invalid ${label}`);
}
function uniqueStringArray(value, label) {
  assert(Array.isArray(value), `${label} must be an array`);
  const seen = new Set();
  for (const item of value) {
    scopedString(item, label);
    assert(!seen.has(item), `duplicate ${label}`);
    seen.add(item);
  }
}
function utf16Compare(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function checkString(value, where) {
  assert(value.normalize("NFC") === value, `non-NFC string at ${where}`);
  assert(!BIDI.test(value), `bidi control at ${where}`);
  for (let i = 0; i < value.length; i += 1) {
    const code = value.charCodeAt(i);
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = value.charCodeAt(i + 1);
      assert(
        next >= 0xdc00 && next <= 0xdfff,
        `unpaired high surrogate at ${where}`,
      );
      i += 1;
    } else {
      assert(
        !(code >= 0xdc00 && code <= 0xdfff),
        `unpaired low surrogate at ${where}`,
      );
    }
  }
}

function numberToken(value) {
  assert(Number.isFinite(value), "non-finite canonical number");
  if (Object.is(value, -0) || value === 0) return "0";
  if (Number.isInteger(value)) return String(value);
  const text = String(value);
  assert(!/[eE]/u.test(text), "independent verifier refuses exponent input");
  return text.replace(/(\.\d*?[1-9])0+$/u, "$1").replace(/\.0+$/u, "");
}

function encode(value, where = "$") {
  if (value === null) return "null";
  if (value === true) return "true";
  if (value === false) return "false";
  if (typeof value === "number") return numberToken(value);
  if (typeof value === "string") {
    checkString(value, where);
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return (
      "[" +
      value.map((item, index) => encode(item, `${where}[${index}]`)).join(",") +
      "]"
    );
  }
  assert(typeof value === "object", `unsupported value at ${where}`);
  const keys = Object.keys(value).sort(utf16Compare);
  return (
    "{" +
    keys
      .map((key) => {
        checkString(key, `${where}.<key>`);
        return JSON.stringify(key) + ":" + encode(value[key], `${where}.${key}`);
      })
      .join(",") +
    "}"
  );
}

function validateFrozenShape(packet) {
  assert(packet && typeof packet === "object" && !Array.isArray(packet), "packet must be object");
  for (const key of REQUIRED_TOP) {
    assert(Object.hasOwn(packet, key), `missing top-level field ${key}`);
  }
  for (const key of Object.keys(packet)) {
    assert(TOP_ALLOWED.has(key), `unknown top-level field ${key}`);
  }
  assert(packet.version === "0.1", "unsupported protocol version");
  assert(typeof packet.id === "string" && packet.id.length > 0, "invalid packet id");
  assert(record(packet.pragmatics), "pragmatics must be object");
  identifier(packet.pragmatics.type, "pragmatics.type");
  assert(record(packet.carrier) && record(packet.audit), "carrier/audit must be objects");
  assert(record(packet.context), "context must be object");
  scopedString(packet.context.thread_id, "context.thread_id");
  assert(Array.isArray(packet.context.references), "context.references must be array");
  for (const reference of packet.context.references) {
    assert(record(reference), "context reference must be object");
    scopedString(reference.packet_id, "context.references[].packet_id");
  }
  assert(
    typeof packet.confidence === "number" &&
      packet.confidence >= 0 &&
      packet.confidence <= 1,
    "invalid confidence",
  );
  assert(Array.isArray(packet.atoms), "atoms must be array");
  assert(Array.isArray(packet.relations), "relations must be array");
  assert(Array.isArray(packet.evidence), "evidence must be array");
  assert(record(packet.output), "output must be object");
  assert(OUTPUT_FORMATS.has(packet.output.format), "unsupported output format");
  if (Object.hasOwn(packet.output, "max_bytes")) {
    assert(Number.isSafeInteger(packet.output.max_bytes) && packet.output.max_bytes >= 1,
      "invalid output.max_bytes");
  }

  const permissions = packet.permissions ?? {};
  assert(
    permissions && typeof permissions === "object" && !Array.isArray(permissions),
    "permissions must be object",
  );
  for (const key of Object.keys(permissions)) {
    assert(PERMISSION_ALLOWED.has(key), `non-core permission field ${key}`);
  }
  if (Object.hasOwn(permissions, "mode")) {
    assert(MODES.has(permissions.mode), "unknown permission mode");
  }
  if (Object.hasOwn(permissions, "scope")) uniqueStringArray(permissions.scope, "permission scope");
  if (Object.hasOwn(permissions, "forbid")) uniqueStringArray(permissions.forbid, "permission forbid");
  for (const flag of ["require_confirmation", "require_review", "require_logging"]) {
    if (Object.hasOwn(permissions, flag)) {
      assert(typeof permissions[flag] === "boolean", `permission ${flag} must be boolean`);
    }
  }
  if (SIDE_EFFECT_MODES.has(permissions.mode)) {
    assert(
      Array.isArray(permissions.scope) && permissions.scope.length > 0,
      "side-effect mode requires explicit scope",
    );
  }

  if (Object.hasOwn(packet.context, "packet_id")) {
    assert(
      packet.context.packet_id === packet.id,
      "context.packet_id must match envelope id",
    );
  }

  const atoms = new Map();
  for (const atom of packet.atoms) {
    assert(record(atom), "atom must be object");
    assert(ATOM_ID.test(atom.id), "invalid atom id");
    assert(ATOM_KINDS.has(atom.kind), "invalid atom kind");
    if (Object.hasOwn(atom, "role")) identifier(atom.role, "atom.role");
    if (Object.hasOwn(atom, "attributes")) assert(record(atom.attributes), "atom.attributes must be object");
    assert(!atoms.has(atom.id), `duplicate atom id ${atom.id}`);
    atoms.set(atom.id, atom);
  }

  const relationIds = new Set();
  for (const relation of packet.relations) {
    assert(record(relation), "relation must be object");
    identifier(relation.type, "relation type");
    if (Object.hasOwn(relation, "id")) assert(RELATION_ID.test(relation.id), "invalid relation id");
    assert(
      CORE_RELATIONS.has(relation.type) || relation.type.includes("."),
      `unknown unnamespaced relation ${relation.type}`,
    );
    if (relation.id !== undefined) {
      assert(!relationIds.has(relation.id), `duplicate relation id ${relation.id}`);
      relationIds.add(relation.id);
    }
    assert(Array.isArray(relation.arguments) && relation.arguments.length > 0,
      "relation arguments must be nonempty array");
    for (const argument of relation.arguments) {
      assert(
        SPECIAL_ARGUMENTS.has(argument) || atoms.has(argument),
        `unresolved relation argument ${argument}`,
      );
    }
  }

  const evidenceIds = new Set();
  for (const evidence of packet.evidence) {
    assert(record(evidence), "evidence must be object");
    assert(EVIDENCE_ID.test(evidence.id), "invalid evidence id");
    assert(EVIDENCE_TYPES.has(evidence.source_type), "invalid evidence source_type");
    if (Object.hasOwn(evidence, "source_ref")) scopedString(evidence.source_ref, "evidence.source_ref");
    if (Object.hasOwn(evidence, "input_hash")) scopedString(evidence.input_hash, "evidence.input_hash");
    if (Object.hasOwn(evidence, "supports")) {
      assert(Array.isArray(evidence.supports), "evidence.supports must be array");
    }
    assert(!evidenceIds.has(evidence.id), `duplicate evidence id ${evidence.id}`);
    evidenceIds.add(evidence.id);
    for (const support of evidence.supports ?? []) {
      if (support.startsWith("r")) {
        assert(relationIds.has(support), `unresolved evidence relation ${support}`);
      } else {
        assert(atoms.has(support), `unresolved evidence atom ${support}`);
        assert(
          atoms.get(support).kind === "proposition",
          `evidence atom support is not proposition ${support}`,
        );
      }
    }
  }
}

function splitTopLevel(text, separator) {
  const parts = [];
  let start = 0;
  let round = 0;
  let square = 0;
  let curly = 0;
  let quoted = false;
  let escaped = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (escaped) escaped = false;
      else if (ch === "\\") escaped = true;
      else if (ch === '"') quoted = false;
      continue;
    }
    if (ch === '"') {
      quoted = true;
      continue;
    }
    if (ch === "(") round += 1;
    else if (ch === ")") round -= 1;
    else if (ch === "[") square += 1;
    else if (ch === "]") square -= 1;
    else if (ch === "{") curly += 1;
    else if (ch === "}") curly -= 1;
    else if (
      ch === separator &&
      round === 0 &&
      square === 0 &&
      curly === 0
    ) {
      parts.push(text.slice(start, i).trim());
      start = i + 1;
    }
    assert(round >= 0 && square >= 0 && curly >= 0, "unbalanced canonical Lattice");
  }
  assert(!quoted && round === 0 && square === 0 && curly === 0, "unbalanced canonical Lattice");
  parts.push(text.slice(start).trim());
  return parts;
}

function validateCanonicalLattice(source) {
  let text = source.replace(/^\ufeff/u, "").trim();
  const named = /^[A-Za-z_][A-Za-z0-9_-]*\s*:/u.exec(text);
  if (named) text = text.slice(named[0].length).trim();

  assert(text.startsWith("[") && text.endsWith("]"), "canonical packet must be framed");
  const core = text.slice(1, -1).trim();
  const segments = splitTopLevel(core, "|");
  assert(segments.length === 8, "canonical Lattice requires exactly eight Octad segments");

  const labels = segments.map((segment) => {
    const match = /^([πARKCκΠEΩ])\s*=/u.exec(segment);
    assert(match, `invalid canonical segment ${segment.slice(0, 12)}`);
    return match[1];
  });
  assert(
    labels.every((label, index) => label === OCTAD_SEGMENTS[index]),
    "canonical Lattice segment order mismatch",
  );

  assert(/^π\s*=\s*\([^)]*\bTYPE\s*=/u.test(segments[0]), "π requires TYPE");
  assert(/^C\s*=\s*\([^)]*\bTHREAD\s*=/u.test(segments[3]), "C requires THREAD");
  assert(/^Ω\s*=\s*\([^)]*\bFORMAT\s*=/u.test(segments[7]), "Ω requires FORMAT");
}

function expectFailure(fn, label) {
  let rejected = false;
  try {
    fn();
  } catch {
    rejected = true;
  }
  assert(rejected, `${label}: expected rejection`);
}

let canonicalBytes = 0;
let positiveJson = 0;
let negativeJson = 0;
let positiveLattice = 0;
let negativeLattice = 0;

for (const relative of MANIFEST.positive_json) {
  const file = path.join(CONF, relative);
  const raw = fs.readFileSync(file);
  const text = raw.toString("utf8");
  assert(!text.startsWith("\ufeff"), `${relative}: canonical vector contains BOM`);
  const parsed = JSON.parse(text);
  validateFrozenShape(parsed);
  const reproduced = Buffer.from(encode(parsed), "utf8");
  assert(
    Buffer.compare(raw, reproduced) === 0,
    `${relative}: independent canonical bytes do not match`,
  );
  canonicalBytes += raw.length;
  positiveJson += 1;
}

for (const testCase of MANIFEST.negative_json) {
  const file = path.join(CONF, testCase.path);
  expectFailure(() => {
    const packet = JSON.parse(fs.readFileSync(file, "utf8"));
    validateFrozenShape(packet);
  }, testCase.path);
  negativeJson += 1;
}

for (const relative of MANIFEST.positive_lattice) {
  validateCanonicalLattice(fs.readFileSync(path.join(CONF, relative), "utf8"));
  positiveLattice += 1;
}

for (const testCase of MANIFEST.negative_lattice) {
  expectFailure(
    () => validateCanonicalLattice(fs.readFileSync(path.join(CONF, testCase.path), "utf8")),
    testCase.path,
  );
  negativeLattice += 1;
}

const baseline = JSON.parse(
  fs.readFileSync(path.join(CONF, MANIFEST.positive_json[0]), "utf8"),
);
for (const field of MANIFEST.noncanonical_permission_fields) {
  const injected = structuredClone(baseline);
  const value =
    field === "delegation"
      ? { parent_packet: "p0" }
      : field === "capabilities" || field === "resources"
        ? ["commit"]
        : "noncore";
  injected.permissions[field] = value;
  expectFailure(() => validateFrozenShape(injected), `non-core permission ${field}`);
}

// Independent semantic mutation probes guard against a verifier that only
// recognizes the checked-in negative fixture patterns.
const mutationCases = [
  ["unknown atom kind", p => { p.atoms = [{ id: "a0", kind: "invalid" }]; }],
  ["invalid atom id", p => { p.atoms = [{ id: "bad", kind: "entity" }]; }],
  ["empty relation arguments", p => { p.relations = [{ type: "is", arguments: [] }]; }],
  ["non-string permission scope", p => { p.permissions = { mode: "COMMIT", scope: [42] }; }],
  ["empty context thread", p => { p.context.thread_id = ""; }],
  ["unknown evidence source", p => { p.evidence = [{ id: "e0", source_type: "bad" }]; }],
  ["unknown output format", p => { p.output.format = "BAD"; }],
  ["non-object carrier", p => { p.carrier = "bad"; }],
  ["invalid relation namespace", p => { p.relations = [{ type: ".", arguments: ["SELF"] }]; }],
];
for (const [label, mutate] of mutationCases) {
  const modified = structuredClone(baseline);
  mutate(modified);
  expectFailure(() => validateFrozenShape(modified), label);
}

process.stdout.write(
  JSON.stringify({
    implementation: "independent-js-v0.1",
    manifest: MANIFEST.version,
    positive_json: positiveJson,
    negative_json: negativeJson,
    positive_lattice: positiveLattice,
    negative_lattice: negativeLattice,
    canonical_bytes: canonicalBytes,
    noncore_permission_fields: MANIFEST.noncanonical_permission_fields.length,
    semantic_mutation_cases: mutationCases.length,
    status: "passed",
  }) + "\n",
);
