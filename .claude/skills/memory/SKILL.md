---
name: memory
description: Save valuable insights from the current session to storage
user-invocable: true
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
argument-hint: ["nota-específica-opcional"]
---

# Comando Memory

Salvar insights da sessão em `.claude/storage/` para referência futura (diretório criado automaticamente no primeiro uso).

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Uso

```bash
/memory                           # Salvar insights da sessão atual
/memory "nota específica"         # Salvar com contexto específico
```

---

## O Que Faz

1. **Analisa** a conversa atual em busca de insights valiosos
2. **Comprime** para formato de alto sinal (decisões, padrões, armadilhas)
3. **Salva** em `.claude/storage/memory-{AAAA-MM-DD}.md`

---

## Quando Usar

Use `/memory` quando descobrir algo que vale lembrar:

- Decisões não óbvias com justificativa
- Padrões que funcionaram bem
- Armadilhas descobertas
- Decisões de arquitetura
- Esclarecimentos de terminologia

**Não salvar:**

- Detalhes de implementação passo a passo (óbvios pelo código)
- Informações temporárias de debug
- Toda sessão (apenas as valiosas)

---

## Formato de Saída

Cria: `.claude/storage/memory-{AAAA-MM-DD}.md`

```markdown
# Memória: {data}

> {Resumo da sessão em uma frase}

## Decisões Tomadas

| Decisão | Justificativa | Impacto |
| ------- | ------------- | ------- |
| {o quê} | {por quê} | {arquivos afetados} |

## Padrões Descobertos

- {padrão}: {onde aplicado}

## Armadilhas

- {armadilha}: {como evitar}

## Itens em Aberto

- [ ] {item para próxima sessão}
```

---

## Processo

Quando invocado:

1. Escanear conversa por decisões, padrões, armadilhas, itens em aberto
2. Comprimir sem piedade (máx 5 decisões, 3 padrões, 3 armadilhas, 3 itens)
3. Escrever em `.claude/storage/` (criar dir se não existir, anexar se mesma data)

---

## Gate de Qualidade

```text
[ ] Insights são valiosos (não triviais)
[ ] Formato consistente seguido
[ ] Máximo de itens respeitado (5/3/3/3)
[ ] Caminhos de arquivos referenciados quando relevante
[ ] Decisões incluem justificativa
```

---

## Boas Práticas

| Faça | Não Faça |
| ---- | -------- |
| Salvar apenas insights valiosos | Salvar toda sessão |
| Comprimir sem piedade | Escrever resumos longos |
| Referenciar caminhos de arquivos | Duplicar comentários do código |
| Armazenar decisões + justificativa | Armazenar detalhes de implementação |
