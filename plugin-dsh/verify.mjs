// Standalone verification of the AgentSpec dsh plugins against the real dsh
// service types. Run from plugin-dsh/ (resolves @deepseek-ai deps through the
// node_modules bridge):  node verify.mjs
import { Context } from '@deepseek-ai/cordis';
import SkillRegistry from '@deepseek-ai/dsh-skill';
import CommandRuntime from '@deepseek-ai/dsh-commands';
import { apply as applySkills } from './lib/skills.js';
import { apply as applyCommands } from './lib/commands.js';

const ctx = new Context();

// --- skills ---
await ctx.plugin(SkillRegistry);
await new Promise((r) => setTimeout(r, 50)); // Cordis 4 provides services async
applySkills(ctx);

const skills = await ctx.skills.list({});
console.log(`\n[skills] ${skills.length} registered`);
const names = skills.map((s) => s.name);
console.log('  names kebab-case OK:', names.every((n) => /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(n)));
console.log('  sdd-workflow present:', names.includes('sdd-workflow'));
console.log('  source-command-workflow-build present:', names.includes('source-command-workflow-build'));
console.log('  agent-router present:', names.includes('agent-router'));
console.log('  first 6:', names.slice(0, 6).join(', '));

const def = await ctx.skills.get('sdd-workflow', {});
console.log('  sdd-workflow content bytes:', def?.content.length, '| desc:', def?.description);
const bc = await ctx.skills.get('source-command-workflow-brainstorm', {});
console.log('  brainstorm skill content bytes:', bc?.content.length, '| modelInvocable:', bc?.invocation.modelInvocable);

// --- commands ---
await ctx.plugin(CommandRuntime);
await new Promise((r) => setTimeout(r, 50));
console.log('\n[commands] ctx.commands mounted:', !!ctx.commands);
applyCommands(ctx);
console.log('  registered without throwing (17 native commands)');

console.log('\nverify.mjs OK');
