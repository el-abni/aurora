# Aury to Aurora Dossier - Aurora v1.3.0

## Leitura canônica

- `Aury` é a raiz operacional.
- `Aurora` é a camada de decisão e mediação.

Essa leitura é patrimônio estrutural da linha também na `v1.3.0`.

## O que a Aurora herda na v1.3.0

- disciplina de normalização e proteção de tokens;
- leitura mínima de host Linux e probes operacionais;
- experiência acumulada de runtime e observabilidade;
- lição de que contrato pequeno e explícito endurece melhor do que amplitude implícita.
- leitura de que manutenção do host só entra quando policy, execução real, observabilidade e confirmação explícita estão fechadas.
- lição de que orientação pública precisa ser curta, testável e subordinada ao kernel.
- lição de que clarificação de fonte/superfície precisa ensinar sintaxe explícita sem virar descoberta, escolha automática ou fallback.

Isso reaproveita aprendizado real da Aury sem copiar mecanicamente sua superfície.

## O que fica para depois

- qualquer expansão de domínio além do contrato público já aberto;
- qualquer nova relação operacional entre Aurora e uma Aury futura;
- qualquer revisão grande de runtime que exija reabrir superfícies ou backlog lateral.
- qualquer tentativa de usar modelo local para remendar contrato frouxo ou para puxar a Aury para dentro do runtime da Aurora.

## O que nunca deve migrar como implementação

Esta seção registra, de forma direta, o que não deve migrar como implementação.

- Fish como centro do produto;
- gate final copiado mecanicamente da Aury;
- dependência de runtime no checkout da Aury;
- transformação da Aury em frontend da Aurora;
- importação ampla de hábitos, stage pública ou mecânicas históricas só por herança.

## Regra de fronteira

A Aury canônica inspira estrutura, disciplina e leitura operacional.

A Aurora canônica decide, media e publica contrato próprio.

Desde a `v1.0.0`, o modelo local entra como seam propria da Aurora, com autoridade limitada e fallback deterministico. A Aury nao herda esse papel como centro do runtime.

Isso evita um choque já aprendido pelo repositório: herança útil não é licença para copiar molde mecânico nem para reabrir acoplamentos que a linha atual já deixou para trás.
