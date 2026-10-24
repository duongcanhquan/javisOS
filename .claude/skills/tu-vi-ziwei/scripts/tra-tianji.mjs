#!/usr/bin/env node
/**
 * Tra trích dẫn 倪师《天纪》trong vendor (CC BY-NC-SA 4.0).
 * Chỉ dùng cho học tập / phi thương mại. Không đưa nguyên văn vào sản phẩm bán.
 */
import { createInterface } from 'node:readline';
import { createReadStream, existsSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

function stateRoot() {
  return process.env.JAVIS_STATE_DIR || join(homedir(), '.javis');
}

function entriesPath() {
  const lib =
    process.env.ZIWEI_DOUSHU_HOME ||
    join(stateRoot(), 'vendor', 'ziwei-doushu');
  return join(lib, 'docs', 'tianji-ziwei', 'entries.jsonl');
}

function parseArgs(argv) {
  const out = { query: '', limit: 5 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--query') out.query = argv[++i] || '';
    else if (a === '--limit') out.limit = Number(argv[++i] || 5);
    else if (a === '--help' || a === '-h') out.help = true;
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.query) {
    console.log(
      `Usage: node tra-tianji.mjs --query "化忌" [--limit 5]\nLicense: CC BY-NC-SA 4.0 (non-commercial).`,
    );
    process.exit(args.help ? 0 : 1);
  }
  const path = entriesPath();
  if (!existsSync(path)) {
    console.error(
      `[tra-tianji] thiếu ${path}. Chạy ensure-ziwei.sh trước.`,
    );
    process.exit(1);
  }

  const q = args.query.trim();
  const limit = Math.max(1, args.limit || 5);
  const hits = [];
  const rl = createInterface({ input: createReadStream(path, 'utf8'), crlfDelay: Infinity });
  for await (const line of rl) {
    if (!line.trim()) continue;
    let row;
    try {
      row = JSON.parse(line);
    } catch {
      continue;
    }
    const blob = [row.quote, row.h2, row.h3, row.note, row.book]
      .filter(Boolean)
      .join('\n');
    if (blob.includes(q)) {
      hits.push({
        book: row.book,
        h2: row.h2,
        h3: row.h3,
        quote: row.quote,
        note: row.note || undefined,
        bvid: row.bvid,
        t: row.t_hms,
      });
      if (hits.length >= limit) break;
    }
  }

  const payload = {
    license: 'CC BY-NC-SA 4.0',
    commercialUse: false,
    attribution: '倪海厦《天纪》quotes via Renhuai123/ziwei-doushu docs/tianji-ziwei',
    warning:
      'Chỉ học tập / phi thương mại. Không copy nguyên văn vào báo cáo bán hàng hoặc sản phẩm thương mại.',
    query: q,
    count: hits.length,
    hits,
  };
  process.stdout.write(JSON.stringify(payload, null, 2) + '\n');
}

main();
