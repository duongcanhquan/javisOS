#!/usr/bin/env node
/**
 * Lập lá số Tử Vi qua iztro (cùng engine lõi với ziwei-doushu).
 * Runtime: $JAVIS_STATE_DIR/vendor/javis-ziwei-runtime (ensure-ziwei.sh).
 */
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { homedir } from 'node:os';
import { pathToFileURL } from 'node:url';

function stateRoot() {
  return process.env.JAVIS_STATE_DIR || join(homedir(), '.javis');
}

function runtimeRoot() {
  return (
    process.env.ZIWEI_RUNTIME_HOME ||
    join(stateRoot(), 'vendor', 'javis-ziwei-runtime')
  );
}

function loadIztro() {
  const root = runtimeRoot();
  const pkg = join(root, 'node_modules', 'iztro');
  if (!existsSync(pkg)) {
    console.error(
      `[lap-la-so] chưa có iztro tại ${pkg}. Chạy: bash .claude/skills/tu-vi-ziwei/scripts/ensure-ziwei.sh`,
    );
    process.exit(1);
  }
  const require = createRequire(pathToFileURL(join(root, 'package.json')).href);
  return require('iztro');
}

/** Giờ đồng hồ → chỉ số giờ chi 0..11 (Tý=23-01). */
export function clockToBranch(hour, minute = 0) {
  const h = Number(hour);
  const m = Number(minute) || 0;
  if (!Number.isInteger(h) || h < 0 || h > 23) {
    throw new RangeError(`hour đồng hồ phải 0..23, nhận: ${hour}`);
  }
  if (m < 0 || m > 59) {
    throw new RangeError(`minute phải 0..59, nhận: ${minute}`);
  }
  // 23:00-00:59 → Tý (0); mỗi 2 giờ một chi
  const totalMin = h * 60 + m;
  if (totalMin >= 23 * 60 || totalMin < 60) return 0;
  return Math.floor((totalMin - 60) / 120) + 1;
}

function parseArgs(argv) {
  const out = {
    date: null,
    hour: null,
    minute: 0,
    branch: null,
    gender: null,
    name: '',
    lang: 'vi-VN',
    outPath: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => {
      i += 1;
      return argv[i];
    };
    if (a === '--date') out.date = next();
    else if (a === '--hour') out.hour = Number(next());
    else if (a === '--minute') out.minute = Number(next());
    else if (a === '--branch') out.branch = Number(next());
    else if (a === '--gender') out.gender = String(next()).toLowerCase();
    else if (a === '--name') out.name = next() || '';
    else if (a === '--lang') out.lang = next() || 'vi-VN';
    else if (a === '--out') out.outPath = next();
    else if (a === '--help' || a === '-h') out.help = true;
  }
  return out;
}

function usage() {
  console.log(`Usage:
  node lap-la-so.mjs --date YYYY-M-D --hour H [--minute M] --gender male|female|nam|nu \\
    [--name NAME] [--lang vi-VN|zh-CN] [--out path.json]

  hoặc --branch 0..11 thay cho --hour/--minute (0=Tý … 11=Hợi)
`);
}

function normalizeGender(g) {
  const s = String(g || '').toLowerCase();
  if (['male', 'nam', 'm', '男'].includes(s)) return { iztro: '男', key: 'male' };
  if (['female', 'nu', 'nữ', 'f', '女'].includes(s)) return { iztro: '女', key: 'female' };
  throw new Error(`gender phải male/female (nam/nu); nhận: ${g}`);
}

function palaceBrief(p) {
  if (!p) return null;
  return {
    name: p.name,
    isOriginalPalace: p.isOriginalPalace,
    heavenlyStem: p.heavenlyStem,
    earthlyBranch: p.earthlyBranch,
    majorStars: (p.majorStars || []).map((s) => ({
      name: s.name,
      brightness: s.brightness,
      mutagen: s.mutagen,
    })),
    minorStars: (p.minorStars || []).map((s) => ({
      name: s.name,
      brightness: s.brightness,
      mutagen: s.mutagen,
    })),
    adjectiveStars: (p.adjectiveStars || []).slice(0, 12).map((s) => ({
      name: s.name,
      brightness: s.brightness,
    })),
    decadal: p.decadal
      ? {
          range: p.decadal.range,
          heavenlyStem: p.decadal.heavenlyStem,
          earthlyBranch: p.decadal.earthlyBranch,
        }
      : undefined,
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    process.exit(0);
  }
  if (!args.date || args.gender == null) {
    usage();
    process.exit(1);
  }

  let branch = args.branch;
  if (branch == null) {
    if (args.hour == null) {
      console.error('Cần --hour hoặc --branch');
      process.exit(1);
    }
    branch = clockToBranch(args.hour, args.minute);
  }
  if (!Number.isInteger(branch) || branch < 0 || branch > 11) {
    console.error(`branch phải 0..11; nhận: ${branch}`);
    process.exit(1);
  }

  const gender = normalizeGender(args.gender);
  const { astro } = loadIztro();
  const dateParts = String(args.date).split(/[-/]/).map((x) => Number(x));
  if (dateParts.length !== 3 || dateParts.some((n) => !Number.isFinite(n))) {
    console.error(`--date phải YYYY-M-D; nhận: ${args.date}`);
    process.exit(1);
  }
  const [y, mo, d] = dateParts;
  const solar = `${y}-${mo}-${d}`;

  const a = astro.bySolar(solar, branch, gender.iztro, true, args.lang);

  const palaces = (a.palaces || []).map(palaceBrief);
  const ming = a.palace ? a.palace('命宫') || a.palace('Mệnh') : null;

  const chart = {
    engine: 'iztro',
    upstream: 'https://github.com/Renhuai123/ziwei-doushu',
    generatedAt: new Date().toISOString(),
    input: {
      solarDate: solar,
      clockHour: args.hour,
      clockMinute: args.minute,
      hourBranch: branch,
      gender: gender.key,
      name: args.name || undefined,
      lang: args.lang,
    },
    summary: {
      gender: a.gender,
      solarDate: a.solarDate,
      lunarDate: a.lunarDate,
      chineseDate: a.ChineseDate,
      time: a.time,
      timeRange: a.timeRange,
      soulPalaceBranch: a.earthlyBranchOfSoulPalace,
      bodyPalaceBranch: a.earthlyBranchOfBodyPalace,
      soul: a.soul,
      body: a.body,
      fiveElementsClass: a.fiveElementsClass,
    },
    mingGong: palaceBrief(ming),
    palaces,
  };

  const text = JSON.stringify(chart, null, 2);
  if (args.outPath) {
    const abs = resolve(args.outPath);
    mkdirSync(dirname(abs), { recursive: true });
    writeFileSync(abs, text, 'utf8');
    console.error(`[lap-la-so] wrote ${abs}`);
  }
  process.stdout.write(text + '\n');
}

main();
