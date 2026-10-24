#!/usr/bin/env node
/**
 * Tra cổ thư công cộng trong vendor ziwei-doushu (骨髓赋 / 全集 / 全书).
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

function stateRoot() {
  return process.env.JAVIS_STATE_DIR || join(homedir(), '.javis');
}

function libRoot() {
  return (
    process.env.ZIWEI_DOUSHU_HOME ||
    join(stateRoot(), 'vendor', 'ziwei-doushu')
  );
}

function classicsDataDir() {
  return join(libRoot(), 'lib', 'classics', 'data');
}

/** Rút các đoạn text: '...' từ file .ts dữ liệu sách. */
function extractParagraphs(filePath, bookSlug) {
  const src = readFileSync(filePath, 'utf8');
  const titleMatch = src.match(/title:\s*'([^']+)'/);
  const bookTitle = titleMatch ? titleMatch[1] : bookSlug;
  const paras = [];
  const re =
    /id:\s*'([^']+)'[\s\S]*?idx:\s*(\d+)[\s\S]*?text:\s*'((?:\\'|[^'])*)'/g;
  let m;
  while ((m = re.exec(src)) !== null) {
    paras.push({
      book: bookTitle,
      slug: bookSlug,
      id: m[1],
      idx: Number(m[2]),
      text: m[3].replace(/\\'/g, "'"),
    });
  }
  return paras;
}

function loadAll(bookFilter) {
  const dir = classicsDataDir();
  if (!existsSync(dir)) {
    console.error(
      `[tra-co-thu] chưa có cổ thư tại ${dir}. Chạy ensure-ziwei.sh trước.`,
    );
    process.exit(1);
  }
  const files = readdirSync(dir).filter((f) => f.endsWith('.ts'));
  const all = [];
  for (const f of files) {
    const slug = f.replace(/\.ts$/, '');
    if (bookFilter && slug !== bookFilter && !bookFilter.includes(slug)) continue;
    all.push(...extractParagraphs(join(dir, f), slug));
  }
  return all;
}

function parseArgs(argv) {
  const out = { query: '', book: null, limit: 8 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--query') out.query = argv[++i] || '';
    else if (a === '--book') out.book = argv[++i];
    else if (a === '--limit') out.limit = Number(argv[++i] || 8);
    else if (a === '--help' || a === '-h') out.help = true;
  }
  return out;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.query) {
    console.log(
      `Usage: node tra-co-thu.mjs --query "紫微" [--book gusuifu|quanji|quanshu] [--limit 8]`,
    );
    process.exit(args.help ? 0 : 1);
  }
  const q = args.query.trim();
  const hits = loadAll(args.book)
    .filter((p) => p.text.includes(q))
    .slice(0, Math.max(1, args.limit || 8));

  const payload = {
    license: 'public-domain-classics',
    query: q,
    book: args.book || 'all',
    count: hits.length,
    hits,
  };
  process.stdout.write(JSON.stringify(payload, null, 2) + '\n');
}

main();
