// Independent dependency-free LSTP v0.1 canonical JSON verifier.
//
// This implementation deliberately does not import or invoke the Python package.
// It exercises the shared canonical byte fixture using JavaScript's own parser
// and a separately implemented canonical encoder.

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..");
const VECTOR_DIR = path.join(ROOT, "conformance", "v0.1", "positive");

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

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
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

  // Shared v0.1 vectors intentionally stay within exactly representable
  // non-exponent decimal values. Reject rather than guess outside that profile.
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
    return "[" + value.map((item, index) => encode(item, `${where}[${index}]`)).join(",") + "]";
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
  for (const key of REQUIRED_TOP) {
    assert(Object.hasOwn(packet, key), `missing top-level field ${key}`);
  }
  for (const key of Object.keys(packet)) {
    assert(TOP_ALLOWED.has(key), `unknown top-level field ${key}`);
  }
  assert(packet.version === "0.1", "unsupported protocol version");
  assert(typeof packet.pragmatics?.type === "string", "missing pragmatics.type");
  assert(typeof packet.context?.thread_id === "string", "missing context.thread_id");
  assert(Array.isArray(packet.context?.references), "context.references must be array");
  assert(packet.confidence >= 0 && packet.confidence <= 1, "invalid confidence");
  assert(Array.isArray(packet.atoms), "atoms must be array");
  assert(Array.isArray(packet.relations), "relations must be array");
  assert(Array.isArray(packet.evidence), "evidence must be array");
  assert(typeof packet.output?.format === "string", "missing output.format");

  const modes = new Set(["RO", "SUGGEST", "PREVIEW", "RW", "EXEC", "COMMIT"]);
  if (Object.hasOwn(packet.permissions ?? {}, "mode")) {
    assert(modes.has(packet.permissions.mode), "unknown permission mode");
  }
  for (const key of Object.keys(packet.permissions ?? {})) {
    assert(PERMISSION_ALLOWED.has(key), `non-core permission field ${key}`);
  }
}

const vectorNames = fs
  .readdirSync(VECTOR_DIR)
  .filter((name) => name.endsWith(".json"))
  .sort();
assert(vectorNames.length >= 2, "independent verifier requires multiple vectors");

let totalBytes = 0;
let firstPacket = null;
for (const name of vectorNames) {
  const vector = path.join(VECTOR_DIR, name);
  const raw = fs.readFileSync(vector);
  const text = raw.toString("utf8");
  assert(!text.startsWith("\ufeff"), `${name}: canonical vector must not contain BOM`);
  const parsed = JSON.parse(text);
  validateFrozenShape(parsed);
  const reproduced = Buffer.from(encode(parsed), "utf8");
  assert(
    Buffer.compare(raw, reproduced) === 0,
    `${name}: independent canonical bytes do not match shared vector`,
  );
  totalBytes += raw.length;
  firstPacket ??= parsed;
}

// Independent negative check for the resolved GOV-EXT boundary.
const injected = structuredClone(firstPacket);
injected.permissions.authorization_ref = "host-controlled";
let rejected = false;
try {
  validateFrozenShape(injected);
} catch {
  rejected = true;
}
assert(rejected, "host-only permission field was accepted as canonical v0.1");

process.stdout.write(
  JSON.stringify({
    implementation: "independent-js-v0.1",
    vectors: vectorNames,
    canonical_bytes: totalBytes,
    gov_ext_rejected: true,
    status: "passed",
  }) + "\n",
);
