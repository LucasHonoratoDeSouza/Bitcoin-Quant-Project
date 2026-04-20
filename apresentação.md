# Apresentacao Tecnica do Bitcoin Quant Project

## 1. Objetivo do Sistema

O projeto implementa uma engine quantitativa para alocacao em Bitcoin com foco em:

- crescimento de patrimonio em BTC e USD no longo prazo;
- controle de drawdown via regras de alocacao dinamica;
- tomada de decisao reproduzivel e auditavel;
- promocao de mudancas para producao apenas com evidencia objetiva out-of-sample.

A metrica operacional principal e o alpha contra Buy and Hold:

$$
\alpha_{BTC} = ROI_{estrategia} - ROI_{buy\&hold}
$$

## 2. Arquitetura Funcional

O sistema segue um pipeline em camadas:

1. Coleta de dados: precos, on-chain, macro, sentimento, derivativos.
2. Processamento de features: normalizacao, flags de regime e contexto de mercado.
3. Scoring quantitativo: pontuacoes Long Term (LT) e Medium Term (MT).
4. Traducao score->ordem: portfolio managers transformam score em alocacao alvo.
5. Execucao simulada: custos, slippage implícito por bps, debt carry e rebalance.
6. Contabilidade: estado de carteira, historico, relatorios e atualizacao do README.
7. Governanca de producao: gate OOS decide qual modelo pode ficar ativo.

Arquivos centrais:

- `src/strategy/score.py`
- `src/strategy/legacy_score.py`
- `src/execution/portfolio_manager.py`
- `src/execution/confidence_portfolio_manager.py`
- `src/execution/advanced_portfolio_manager.py`
- `src/execution/accounting.py`
- `src/execution/production_gate.py`
- `src/main_paper_trading.py`

## 3. Fluxo Diario de Producao

Sequencia de execucao diaria:

1. `download`: coleta snapshot bruto do dia.
2. `process`: constroi features e flags processadas.
3. `paper`: calcula score, decide ordem, atualiza estado e gera relatorio.

A rotina de paper trading faz:

- resolve modelo ativo em `data/signals/production_gate.json`;
- instancia scorer + allocation engine correspondente;
- calcula LT/MT e decide ordem (`BUY`/`SELL`/`None`);
- executa contabilmente com debt carry e atualiza historico.

Se o gate nao existir ou estiver invalido, o sistema faz fallback seguro para:

- `production_legacy_cooldown1`.

## 4. Bloco de Sinais Quantitativos

## 4.1 LegacyQuantScorer (baseline de producao)

Estrutura:

- LT combina valuation on-chain, ciclo de halving e macro;
- MT combina direcao de tendencia, extensao de preco e sentimento.

Forma geral:

$$
Score_{LT} = 100 \cdot (w_1 \cdot OnChain + w_2 \cdot Cycle + w_3 \cdot Macro)
$$

$$
Score_{MT} = 100 \cdot (v_1 \cdot Trend + v_2 \cdot Sentiment + v_3 \cdot Extension + v_4 \cdot Seasonality)
$$

## 4.2 AdvancedQuantScorer (pesquisa)

Adiciona:

- transformacoes suaves tipo sigmoid;
- penalidades de regime (derivativos, inflacao, correlacao);
- maior sensibilidade a divergencia trend x momentum.

O objetivo e reduzir comportamento binario (all-in/all-out), mantendo API compativel.

## 5. Motores de Alocacao

## 5.1 PortfolioManager (regra principal)

Converte LT/MT em alocacao alvo com histerese e cooldown.

Comportamentos principais:

- Super Bull: pode alavancar ate 2x (score extremo);
- Strong Buy: 100% BTC;
- Bear defensivo: moonbag de 10%;
- Extreme Bear: exit completo;
- Accumulate/Sell Rally: ajustes dinamicos por intensidade do score.

Mecanismos de estabilidade:

- threshold dinamico de trade (percentual do patrimonio);
- cooldown temporal para reduzir overtrading.

## 5.2 ConfidencePortfolioManager (pesquisa melhorada)

Nova versao implementada inclui:

- score de confianca LT/MT;
- risk budget dependente de regime;
- ajuste assimetrico para cenarios conflitantes;
- threshold e cooldown adaptativos por confianca.

Em notacao simplificada:

$$
Target_{adj} = Current + \gamma(Confidence, RiskBudget) \cdot (Target_{raw} \cdot RiskBudget - Current)
$$

Isso preserva defesa no downside e ainda captura tendencia quando ha concordancia forte.

## 6. Simulador e Contabilidade

`PortfolioSimulator` modela:

- custo de transacao por lado em bps;
- financiamento de divida em base diaria;
- impacto de compra/venda em cash, BTC e debt;
- equity diario e metricas de risco/retorno.

Metricas reportadas:

- total return, CAGR;
- max drawdown;
- Sharpe, Sortino, Calmar;
- volatilidade anualizada;
- turnover, trades/ano, alavancagem media e maxima.

## 7. Governanca de Promocao para Producao

A promocao agora e objective-driven:

- walk-forward purged+embargo com cobertura minima de folds;
- bootstrap de significancia em retornos OOS diarios;
- artefato de gate em `data/signals/production_gate.json`.

Regra pratica:

1. candidato precisa passar criterios de desempenho OOS;
2. precisa de evidencia estatistica minima vs incumbent;
3. precisa manter robustez contra BnH;
4. so entao pode virar modelo ativo.

## 8. Camada de Validacao Estocastica (Nova)

Arquivo principal:

- `tests/backtest/stochastic_calculus_validation.py`

A validacao estocastica testa o algoritmo completo (score + alocacao + execucao) em caminhos sinteticos gerados por SDE.

## 8.1 Modelo estocastico

Foi implementado um modelo regime-switching jump-diffusion:

$$
dS_t = \mu_{r_t} S_t dt + \sigma_{r_t} S_t dW_t + S_t (e^{J_t} - 1) dN_t
$$

onde:

- $r_t$ segue cadeia de Markov (regimes de baixa/media/alta volatilidade);
- $W_t$ e movimento Browniano;
- $N_t$ e processo de Poisson para saltos;
- $J_t$ e tamanho de salto (normal) por evento.

Parametros calibrados do historico:

- drift e vol anualizados por regime;
- matriz de transicao entre regimes;
- intensidade de saltos ($\lambda$) e distribuicao de jump size.

## 8.2 Teste de ponta a ponta

Para cada caminho Monte Carlo:

1. reconstrucao de features sinteticas (mvrv_zscore, mayer, rup, sopr, fear\&greed, macro proxies, flags);
2. reavaliacao dos scorers;
3. reexecucao dos portfolio managers;
4. coleta de distribuicoes de retorno, sharpe e drawdown por modelo.

## 8.3 Graficos gerados

Gerados em `reports/stochastic/figures/`:

- fan chart Monte Carlo (dispersao de trajetorias);
- superficie 3D Drift x Volatilidade x Retorno esperado;
- nuvem 3D de risco-retorno por caminho e por modelo;
- heatmap da matriz de transicao de regimes.

Relatorio final:

- `docs/backtesting-reports/stochastic_validation.md`

## 9. Interpretacao Quantitativa dos Resultados

Como ler os resultados estocasticos:

1. Mean Return alto com CVaR muito negativo indica cauda pesada.
2. P(Beat BnH) > 50% sugere dominancia probabilistica, nao garantia.
3. Superficie 3D mostra elasticidade da estrategia a drift/vol.
4. Nuvem 3D separa clusters de regime favoravel e hostil.

## 10. Limites e Cuidados

- Features sinteticas preservam estrutura economica, mas nao replicam toda microestrutura real.
- Saltos gaussianos sao simplificacao; eventos extremos reais podem ter caudas ainda mais pesadas.
- Evidencia estocastica complementa, mas nao substitui, OOS historico purgado e forward testing real.

## 11. Roadmap Quantitativo Imediato

1. Inserir Heston com vol estocastica latente para comparar com jump-diffusion atual.
2. Adicionar controle de multipla comparacao (SPA / White Reality Check) no bloco estocastico.
3. Integrar intervalos de confianca bayesianos para probabilidade de outperform vs BnH.
4. Incluir attribution por fator (valuation/macro/trend) para decompor alpha e risco.

## 12. Comandos de Reproducao

```bash
make backtest
make backtest-subperiod
make backtest-walkforward
make backtest-robustness
make backtest-stochastic
```

Ou diretamente:

```bash
python tests/backtest/stochastic_calculus_validation.py
```

## 13. Conclusao

O modelo atual combina:

- regras transparentes e auditaveis,
- governanca estatistica para promocoes,
- validacao historica OOS,
- e estresse estocastico multirregime com visualizacao avancada.

Isso transforma a estrategia de um conjunto de heuristicas para um processo quantitativo disciplinado, reproduzivel e com controle formal de risco de promocao.
