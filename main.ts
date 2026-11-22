//!/usr/bin/env node
/**
 * make.fun entry program for news-image-20261122.
 * Copies the finished entry.png into MAKEFUN_OUTPUT_DIR (/output in the grader)
 * and verifies the copy is byte-identical and gate-compliant (PNG, ≤1 MiB, ≤1024×1024).
 */

import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(here, "entry.png");
const outputDir = resolve(process.env.MAKEFUN_OUTPUT_DIR ?? "/output");
const destPath = join(outputDir, "entry.png");

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const MAX_BYTES = 1_048_576;
const MAX_DIM = 1024;

function sha256(bytes: Buffer): string {
  return createHash("sha256").update(bytes).digest("hex");
}

function fail(message: string): never {
  throw new Error(`entry.png validation failed: ${message}`);
}

mkdirSync(outputDir, { recursive: true });

const sourceBytes = readFileSync(sourcePath);
if (sourceBytes.length > MAX_BYTES) fail(`file ${sourceBytes.length} bytes > ${MAX_BYTES} (1 MiB)`);
if (!sourceBytes.subarray(0, 8).equals(PNG_SIGNATURE)) fail("not a PNG file");

writeFileSync(destPath, sourceBytes);

const writtenBytes = readFileSync(destPath);
if (writtenBytes.length !== sourceBytes.length) fail("byte length mismatch after write");
if (!writtenBytes.equals(sourceBytes)) fail("byte content mismatch after write");

// quick IHDR dimension check
const ihdrStart = writtenBytes.indexOf(Buffer.from("IHDR"));
if (ihdrStart >= 0) {
  const width = writtenBytes.readUInt32BE(ihdrStart + 4);
  const height = writtenBytes.readUInt32BE(ihdrStart + 8);
  if (width > MAX_DIM || height > MAX_DIM) fail(`image ${width}×${height} > ${MAX_DIM}×${MAX_DIM}`);
}

const digest = sha256(sourceBytes);
console.log(`OK  ${digest}  ${sourceBytes.length} bytes`);