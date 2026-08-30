// AgentSpec human commands — a dsh `ctx.commands` plugin. Each registered
// slash command reads its command template (shipped under ../assets/commands),
// rewrites AgentSpec content references to the bundle's assets root, injects
// the result into the receiving agent's next request, and returns a direct
// CommandResult. This reproduces AgentSpec's slash-command UX in dsh.
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createUserMessage } from '@deepseek-ai/dsh-llm';

export const name = 'agentspec-commands';
export const inject = ['commands'];

const ASSETS_DIR = fileURLToPath(new URL('../assets/', import.meta.url));
const COMMANDS_DIR = path.join(ASSETS_DIR, 'commands');

// Native slash commands registered against dsh's `ctx.commands`. Every other
// AgentSpec command stays available as a model-invocable skill.
const NATIVE_COMMANDS = [
  // SDD workflow (the "same commands")
  'brainstorm', 'define', 'define-m', 'design', 'design-m', 'build',
  'continue', 'ship', 'iterate', 'create-pr', 'work',
  // Core utilities
  'status', 'memory', 'sync-context', 'readme-maker', 'meeting', 'build-slides',
];

const FRONTMATTER_RE = /^---\n[\s\S]*?\n---\n/;

/** Read a command template and its frontmatter description. */
async function loadTemplate(commandName) {
  const file = path.join(COMMANDS_DIR, `${commandName}.md`);
  const text = await readFile(file, 'utf8');
  const fm = FRONTMATTER_RE.exec(text);
  let description = commandName;
  if (fm) {
    const desc = fm[0].match(/^description:\s*(.+)$/m);
    if (desc) description = desc[1].trim().replace(/^["']|["']$/g, '');
  }
  const body = text.replace(FRONTMATTER_RE, '').trim();
  return { description, body };
}

/**
 * Rewrite AgentSpec content references so a dsh agent can read them:
 * templates/contracts/agents resolve to the bundle assets root; SDD output
 * dirs stay workspace-relative (`.claude/sdd/...`) exactly as in AgentSpec.
 */
function rewriteContentRefs(body) {
  return body
    .replace(/\$\{CLAUDE_PLUGIN_ROOT\}\/sdd\/templates\//g, `${ASSETS_DIR}/sdd/templates/`)
    .replace(/\$\{CLAUDE_PLUGIN_ROOT\}\/sdd\/architecture\//g, `${ASSETS_DIR}/sdd/architecture/`)
    .replace(/\$\{CLAUDE_PLUGIN_ROOT\}\/agents\//g, `${ASSETS_DIR}/agents/`)
    .replace(/\$\{CLAUDE_PLUGIN_ROOT\}\//g, `${ASSETS_DIR}/`)
    .replace(/\.claude\/sdd\/templates\//g, `${ASSETS_DIR}/sdd/templates/`)
    .replace(/\.claude\/sdd\/architecture\//g, `${ASSETS_DIR}/sdd/architecture/`)
    .replace(/\.claude\/agents\//g, `${ASSETS_DIR}/agents/`);
}

/** Build the full prompt injected into the agent for one command invocation. */
function buildPrompt(commandName, body, rawInput) {
  const preamble = [
    `# AgentSpec command: /${commandName}`,
    '',
    `You are executing the AgentSpec \`/${commandName}\` command.`,
    '',
    'Content root (templates, contracts, agents):',
    `\`${ASSETS_DIR}\``,
    '',
    'SDD output documents are written to the workspace:',
    '- Features: `.claude/sdd/features/`',
    '- Reports:  `.claude/sdd/reports/`',
    '- Archive:  `.claude/sdd/archive/{FEATURE}/`',
    '',
    'Command argument:',
    `\`\`\``,
    rawInput.trim(),
    '```',
    '',
    'Follow the command process below. Generated SDD documents are written in',
    'pt-BR; technical terms, commands, paths, and agent names stay in English.',
    '',
    '---',
    '',
  ].join('\n');
  return `${preamble}${rewriteContentRefs(body)}\n`;
}

export function apply(ctx) {
  for (const commandName of NATIVE_COMMANDS) {
    ctx.commands.register({
      name: commandName,
      description: `AgentSpec /${commandName} — see template in bundle assets`,
      input: { hint: 'argumentos do comando (ex.: nome da feature / caminho do doc)' },
      handler: async ({ agent, rawInput }) => {
        try {
          const { body } = await loadTemplate(commandName);
          const prompt = buildPrompt(commandName, body, rawInput);
          agent.inject(
            createUserMessage({
              content: [{ type: 'text', text: prompt }],
              source: { kind: 'plugin', plugin: 'agentspec-dsh', form: 'instructions' },
            }),
          );
          return {
            kind: 'success',
            text: `/${commandName} iniciado${rawInput.trim() ? `: ${rawInput.trim()}` : ''}.`,
          };
        } catch (error) {
          return { kind: 'error', text: `/${commandName} falhou: ${String(error)}` };
        }
      },
    });
  }
}
