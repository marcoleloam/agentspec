// AgentSpec skills provider — a dsh `ctx.skills` provider that serves the
// SKILL.md bundles shipped under ../assets/skills. Makes every AgentSpec skill
// (sdd-workflow, source-command-*, authoring, github, KB, ...) model-invocable
// through dsh's native `skill` tool, with no filesystem/config dependency.
import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { isSkillName } from '@deepseek-ai/dsh-skill';

export const name = 'agentspec-skills';
export const inject = ['skills'];

const providerName = 'agentspec';
const ASSETS_DIR = fileURLToPath(new URL('../assets/skills/', import.meta.url));

// `---\n...\n---` frontmatter block at the top of a SKILL.md.
const FRONTMATTER_RE = /^---\n([\s\S]*?)\n---\n/;

/** Split a SKILL.md into its YAML frontmatter keys and markdown body. */
function parseSkill(text) {
  const match = FRONTMATTER_RE.exec(text);
  if (!match) return { metadata: {}, content: text.trim() };
  const metadata = {};
  for (const line of match[1].split('\n')) {
    const idx = line.indexOf(':');
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const raw = line.slice(idx + 1).trim();
    metadata[key] = raw.replace(/^["']|["']$/g, '');
  }
  return { metadata, content: text.slice(match[0].length).trim() };
}

/** A candidate locator: enough to reread the skill body in `get()`. */
function makeLocator(skillPath) {
  return { skillPath };
}

/** Read one skill file and project it into a SkillCandidate. */
async function candidateFromDir(skillDir) {
  const dirPath = path.join(ASSETS_DIR, skillDir.name);
  const skillPath = path.join(dirPath, 'SKILL.md');
  const text = await readFile(skillPath, 'utf8');
  const { metadata } = parseSkill(text);
  const skillName = metadata.name || skillDir.name;
  if (!isSkillName(skillName)) return null;
  return {
    name: skillName,
    description: metadata.description || '',
    whenToUse: metadata.whenToUse,
    invocation: { modelInvocable: true, userInvocable: true },
    source: 'bundled',
    provider: providerName,
    rank: 600, // BUNDLED_SKILL_RANK
    resourceBase: { kind: 'directory', path: dirPath },
    locator: makeLocator(skillPath),
    path: skillPath,
  };
}

export function apply(ctx) {
  ctx.skills.registerProvider(() => ({
    name: providerName,
    async list() {
      const entries = await readdir(ASSETS_DIR, { withFileTypes: true });
      const candidates = [];
      for (const entry of entries) {
        if (!entry.isDirectory()) continue;
        try {
          const candidate = await candidateFromDir(entry);
          if (candidate) candidates.push(candidate);
        } catch {
          // Unreadable/invalid skill — skip; the registry tolerates omissions.
        }
      }
      candidates.sort((a, b) => a.name.localeCompare(b.name));
      return candidates;
    },
    async get(candidate) {
      const text = await readFile(candidate.locator.skillPath, 'utf8');
      const { content } = parseSkill(text);
      return { ...candidate, content };
    },
  }));
}
