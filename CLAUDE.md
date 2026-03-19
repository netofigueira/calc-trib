# ArbiTrib — Calculadora de Arbitragem Tributária PF vs PJ

Micro SaaS de cálculo tributário para assessores de clientes High Net Worth (HNW).
Compara a eficiência entre **Pessoa Física** e **PJ/Holding** considerando Tax Drag,
diferimento tributário e impacto sucessório (ITCMD).

## Stack

- **Backend:** Python + FastAPI (`backend/main.py`, `backend/calculator.py`)
- **Frontend:** Vanilla JS + Chart.js CDN (`frontend/index.html`, `style.css`, `app.js`)
- **Sem banco de dados** no MVP — cálculo stateless por requisição

## Como rodar

```bash
# Instalar dependências
pip install fastapi uvicorn[standard] pydantic

# Iniciar servidor
cd backend
python main.py
# Acesse: http://localhost:8000
```

Ou use o script de conveniência na raiz:

```bash
./run.sh
```

## Estrutura do projeto

```
calc-trib/
├── backend/
│   ├── main.py          # FastAPI: rotas + serve frontend estático
│   ├── calculator.py    # Toda a lógica de cálculo (sem deps externas)
│   └── requirements.txt
├── frontend/
│   ├── index.html       # UI completa (form + resultados)
│   ├── style.css        # Design system com CSS variables
│   └── app.js           # Lógica JS: fetch API, Chart.js, render
├── run.sh               # Script de inicialização
└── CLAUDE.md            # Este arquivo
```

## Arquitetura da calculadora

### API

- `POST /api/calcular` — recebe parâmetros, retorna cálculo completo
- `GET /` — serve o `index.html`
- `GET /static/*` — serve CSS/JS do diretório `frontend/`

### Modelos de cálculo (`calculator.py`)

**PF (Pessoa Física):**
- IR regressivo anual sobre ganhos (15% a 22,5%)
- 10% sobre dividendos distribuídos (Lei 14.754/2023)
- Sem overhead

**PJ Standard:**
- IRPJ + CSLL (34% padrão Lucro Presumido) sobre ganhos anuais
- Overhead operacional fixo anual (contabilidade, jurídico)
- 10% sobre dividendos distribuídos

**PJ com Diferimento:**
- Retorno bruto compõe sem IRPJ anual
- Overhead sai do saldo correntemente
- IRPJ/CSLL calculado sobre o ganho acumulado (saldo - capital) só na liquidação final

**VFL (Valor Futuro Líquido):**
```
VFL = saldo_final_reinvestido + soma_distribuicoes_liquidas_recebidas
```

**ITCMD Progressivo:**
- Faixas proporcionais à alíquota máxima configurada:
  - Até R$200k → 25% do max
  - R$200k–600k → 50% do max
  - R$600k–1,5M → 75% do max
  - Acima R$1,5M → 100% do max
- Base PJ reduzida pelo desconto de quota (valor de livro vs mercado)
- Retorna VFL Pós-Sucessão para ambos os cenários

### Parâmetros de entrada

| Campo | Padrão | Descrição |
|---|---|---|
| `capital_inicial` | R$1.000.000 | Capital investido |
| `rentabilidade_anual` | 10% | Taxa de retorno anual |
| `horizonte_anos` | 10 | Anos de investimento |
| `ir_pf_rate` | 15% | IR regressivo PF (15–22,5%) |
| `ir_pj_rate` | 34% | IRPJ + CSLL |
| `overhead_anual` | R$70.000 | Custos operacionais da holding |
| `taxa_distribuicao` | 50% | % do lucro distribuído como dividendos |
| `usar_deferimento` | false | Modelo de diferimento tributário PJ |
| `taxa_dividendos` | 10% | Alíquota sobre dividendos (Lei 14.754/2023) |
| `itcmd_max_rate` | 8% | Alíquota ITCMD máxima (reforma propõe 16%) |
| `desconto_quota_holding` | 20% | Desconto na base ITCMD das quotas |
| `isento_pf` | false | Aplicação isenta de IR para PF (LCI/LCA/CRI/CRA) |
| `spread_pj` | 0% | Spread da corretora para PJ (título público: 0,5–1%) |
| `ibs_cbs_rate` | 0% | Alíquota IBS+CBS sobre receita bruta da PJ |

### Resposta da API

```json
{
  "vencedor": "Pessoa Física",
  "vfl_pf": 9555240.90,
  "vfl_pj": 7678844.50,
  "diferenca_absoluta": -1876396.40,
  "diferenca_percentual": -19.64,
  "tax_drag_pf": 19.25,
  "tax_drag_pj": 36.67,
  "total_impostos_pf": ...,
  "total_impostos_pj": ...,
  "anos_pf": [...],   // array ano a ano
  "anos_pj": [...],
  "itcmd": {
    "base_pf": ..., "base_pj": ...,
    "itcmd_pf": ..., "itcmd_pj": ...,
    "economia": ...,
    "aliquota_efetiva_pf": ..., "aliquota_efetiva_pj": ...,
    "vfl_pos_sucessao_pf": ..., "vfl_pos_sucessao_pj": ...,
    "vencedor_sucessao": "...",
    "diferenca_sucessao": ...
  },
  "parametros": { ... }
}
```

## Contexto de negócio

- **Público-alvo:** Assessores financeiros e planejadores tributários de HNW
- **Referência legal:** Lei 14.754/2023 (10% dividendos), Lucro Presumido PJ, reforma ITCMD
- **Conceito central:** Tax Drag — quanto do retorno bruto é perdido em impostos.
  A holding raramente ganha na alíquota nominal mas pode ganhar no diferimento e na sucessão.
- **PDFs de referência** (na raiz do projeto, não versionados no git):
  - `comparação (1).pdf` — fluxograma de decisão PF vs Holding
  - `Documento-1.pdf` — parâmetros técnicos detalhados
  - `workbook_v1 (1).xlsx` — planilha com 5 sheets de referência

### Seletor de Classe de Ativo

O frontend tem um dropdown que aplica presets automáticos nos parâmetros:

| Classe | IR PF | Isento PF? | Spread PJ | Notas |
|--------|-------|------------|-----------|-------|
| CDB / Renda Fixa | 15–22,5% | Não | 0% | Caso base |
| LCI / LCA | 0% | **Sim** | 0% | Isento IR na PF, tributado 34% na PJ |
| CRI / CRA | 0% | **Sim** | 0% | Idem LCI/LCA |
| Título Público | 15–22,5% | Não | **0,5%** | PJ sem Tesouro Direto, compra via corretora |
| Personalizado | Ajuste livre | Ajuste livre | Ajuste livre | Tudo editável |

**Cuidado no frontend:** inputs `disabled` são excluídos do `FormData`.
Usar classe CSS `.field-locked` (pointer-events: none + opacity) em vez de `disabled` para travar campos visualmente.

### IBS/CBS (Reforma Tributária)

- Slider 0–28%, incide sobre receita bruta da PJ
- Timeline: 2026 ~1% (teste), pleno 2033 ~26,5%
- Não afeta PF (rendimentos financeiros não são fato gerador)
- Coluna dedicada na tabela detalhada PJ

## Backlog (próximos passos)

- [ ] Gráfico de sensibilidade: múltiplos horizontes simultâneos (5/10/20 anos)
- [ ] Exportar resultado em PDF
- [x] ~~Comparativo por classe de ativo (FII, renda fixa, ações, aluguel direto)~~ — implementado como seletor de presets
- [ ] Autenticação + histórico de simulações salvas
- [x] ~~IBS/CBS (IVA Dual) nas receitas de aluguel e serviços da holding~~ — implementado
- [ ] Modo "apresentação" para mostrar ao cliente em reunião
- [ ] FII como classe de ativo (tributação específica: 20% sobre ganho de capital, dividendos isentos PF)
- [ ] Aluguel direto como classe de ativo (carnê-leão PF vs holding com IBS/CBS)
