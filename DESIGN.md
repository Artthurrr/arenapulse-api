# ArenaPulse — sistema visual

## Direção

O hub usa a linguagem de uma mesa de análise esportiva: informação em linhas, placares compactos,
hierarquia operacional e poucos destaques em âmbar. A interface evita o visual genérico de cards
neon de e-sports e dá prioridade ao fluxo desafio → inscrição → resultado → ranking.

## Tokens

Os tokens canônicos ficam em `tokens.css`; a cópia entregue ao navegador está em
`public/tokens.css`. A paleta usa superfícies carvão azuladas, texto marfim e âmbar como acento.
`Tomorrow` é a fonte de display e `Switzer` é a fonte de leitura.

## Componentes

- `topbar`: marca, busca por comando e sessão.
- `challenge-row`: linha operacional com jogo, descrição, recompensa, prazo e ação.
- `ranking-tower`: classificação contextual do desafio selecionado.
- `player-panel`: resumo autenticado e atalhos de criação e resultado.
- `dialog`: busca, autenticação e formulários transacionais.
- `toast`: retorno curto para erros e efeitos não óbvios.

## Responsividade e acessibilidade

A estrutura começa em uma coluna e passa para duas áreas a partir de 64 rem. Alvos interativos
têm no mínimo 44 px; foco visível, estados desabilitados e redução de movimento são tratados no
CSS. HTML semântico, regiões nomeadas e mensagens `aria-live` apoiam navegação assistiva.

## Evolução

Novas telas devem reutilizar os tokens e manter o acento abaixo de 5% da área. Prefira tabelas,
linhas e painéis operacionais a grades uniformes de cards. Não introduza gradientes neon, sombras
luminosas ou métricas inventadas.
