"""
Calculadora de Arbitragem Tributária - PF vs PJ/Holding
Lógica baseada em:
  - Lei 14.754/2023 (tributação de dividendos 10%)
  - Tabela regressiva IR PF (15% a 22.5%)
  - Lucro Presumido PJ: IRPJ + CSLL (~34%)
  - Modelo de diferimento: imposto diferido até liquidação final
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class AnoData:
    ano: int
    saldo_inicial: float
    retorno_bruto: float
    impostos_ganhos: float
    custos_operacionais: float
    distribuicao_bruta: float
    imposto_distribuicao: float
    reinvestido: float
    saldo_final: float
    patrimonio_acumulado: float  # saldo + distribuições líquidas recebidas até este ano


@dataclass
class CenarioData:
    nome: str
    anos: List[AnoData]
    saldo_final: float
    total_distribuido_liquido: float
    total_impostos: float
    vfl: float  # Valor Futuro Líquido = saldo_final + total_distribuido_liquido


@dataclass
class ResultadoComparativo:
    pf: CenarioData
    pj: CenarioData
    vencedor: str
    diferenca_absoluta: float
    diferenca_percentual: float
    tax_drag_pf: float   # % do retorno bruto total pago em impostos (PF)
    tax_drag_pj: float   # % do retorno bruto total pago em impostos (PJ)
    capital_inicial: float
    rentabilidade_anual: float
    horizonte_anos: int


def _calcular_cenario(
    capital: float,
    r: float,
    n: int,
    taxa_imposto_ganhos: float,
    overhead_anual: float,
    taxa_dividendos: float,
    taxa_distribuicao: float,
    nome: str,
    deferimento: bool = False,
) -> CenarioData:
    """
    Calcula o resultado ano a ano para um cenário (PF ou PJ).

    PF (deferimento=False, overhead=0):
      - Cada ano: IR sobre ganhos (15%-22.5%) + 10% sobre dividendos distribuídos.
      - Saldo cresce sobre o retorno líquido.

    PJ Standard (deferimento=False, overhead>0):
      - Cada ano: IRPJ+CSLL (34%) sobre ganhos + overhead + 10% sobre dividendos.
      - Saldo cresce sobre o lucro líquido após custos.

    PJ Deferimento (deferimento=True):
      - Retorno bruto compõe (sem IRPJ anual), apenas overhead sai e 10% sobre distribuições.
      - Ao final: IRPJ/CSLL aplicado sobre o ganho acumulado (saldo - capital).
      - Simula o benefício de reinvestir o capital que seria pago de IR.

    VFL = saldo_final + total_distribuido_liquido
    """
    saldo = capital
    total_impostos = 0.0
    total_dist_liquida = 0.0
    ganhos_diferidos = 0.0
    anos: List[AnoData] = []

    for ano in range(1, n + 1):
        saldo_inicial = saldo
        retorno_bruto = saldo * r

        if deferimento:
            # Lucro bruto compõe sem tributação imediata; overhead sai do saldo
            impostos_ano = 0.0
            lucro_pos_imposto = retorno_bruto
            ganhos_diferidos += max(0.0, retorno_bruto - overhead_anual)
        else:
            # Tributo anual sobre ganhos
            impostos_ano = retorno_bruto * taxa_imposto_ganhos
            total_impostos += impostos_ano
            lucro_pos_imposto = retorno_bruto - impostos_ano

        # Overhead reduz o lucro disponível (pode ser negativo — corrói o principal)
        lucro_disponivel = lucro_pos_imposto - overhead_anual

        # Distribuição anual de dividendos (só quando há lucro positivo disponível)
        if lucro_disponivel > 0 and taxa_distribuicao > 0:
            dist_bruta = lucro_disponivel * taxa_distribuicao
            imp_div = dist_bruta * taxa_dividendos
            total_impostos += imp_div
            total_dist_liquida += dist_bruta - imp_div
        else:
            dist_bruta = 0.0
            imp_div = 0.0

        reinvestido = lucro_disponivel - dist_bruta - imp_div
        saldo = max(0.0, saldo_inicial + reinvestido)

        anos.append(AnoData(
            ano=ano,
            saldo_inicial=saldo_inicial,
            retorno_bruto=retorno_bruto,
            impostos_ganhos=impostos_ano,
            custos_operacionais=overhead_anual,
            distribuicao_bruta=dist_bruta,
            imposto_distribuicao=imp_div,
            reinvestido=reinvestido,
            saldo_final=saldo,
            patrimonio_acumulado=saldo + total_dist_liquida,
        ))

    # Liquidação final no modo deferimento: paga IRPJ sobre ganho total acumulado
    if deferimento:
        ganho_acumulado = max(0.0, saldo - capital)
        irpj_final = ganho_acumulado * taxa_imposto_ganhos
        total_impostos += irpj_final
        saldo = max(0.0, saldo - irpj_final)
        # Atualiza o último ano com o imposto diferido pago
        if anos:
            anos[-1].saldo_final = saldo
            anos[-1].impostos_ganhos = irpj_final
            anos[-1].patrimonio_acumulado = saldo + total_dist_liquida

    vfl = saldo + total_dist_liquida

    return CenarioData(
        nome=nome,
        anos=anos,
        saldo_final=saldo,
        total_distribuido_liquido=total_dist_liquida,
        total_impostos=total_impostos,
        vfl=vfl,
    )


def calcular_comparativo(
    capital_inicial: float,
    rentabilidade_anual: float,
    horizonte_anos: int,
    ir_pf_rate: float,
    ir_pj_rate: float,
    overhead_anual: float,
    taxa_distribuicao: float,
    usar_deferimento: bool = False,
    taxa_dividendos: float = 0.10,
) -> ResultadoComparativo:

    pf = _calcular_cenario(
        capital=capital_inicial,
        r=rentabilidade_anual,
        n=horizonte_anos,
        taxa_imposto_ganhos=ir_pf_rate,
        overhead_anual=0.0,
        taxa_dividendos=taxa_dividendos,
        taxa_distribuicao=taxa_distribuicao,
        nome="Pessoa Física",
        deferimento=False,
    )

    pj_nome = "PJ/Holding (Deferimento)" if usar_deferimento else "PJ/Holding"
    pj = _calcular_cenario(
        capital=capital_inicial,
        r=rentabilidade_anual,
        n=horizonte_anos,
        taxa_imposto_ganhos=ir_pj_rate,
        overhead_anual=overhead_anual,
        taxa_dividendos=taxa_dividendos,
        taxa_distribuicao=taxa_distribuicao,
        nome=pj_nome,
        deferimento=usar_deferimento,
    )

    diferenca_absoluta = pj.vfl - pf.vfl
    diferenca_percentual = (diferenca_absoluta / pf.vfl * 100) if pf.vfl > 0 else 0.0
    vencedor = "PJ/Holding" if pj.vfl > pf.vfl else "Pessoa Física"

    retorno_total_pf = sum(a.retorno_bruto for a in pf.anos)
    retorno_total_pj = sum(a.retorno_bruto for a in pj.anos)
    tax_drag_pf = (pf.total_impostos / retorno_total_pf * 100) if retorno_total_pf > 0 else 0.0
    tax_drag_pj = (pj.total_impostos / retorno_total_pj * 100) if retorno_total_pj > 0 else 0.0

    return ResultadoComparativo(
        pf=pf,
        pj=pj,
        vencedor=vencedor,
        diferenca_absoluta=diferenca_absoluta,
        diferenca_percentual=diferenca_percentual,
        tax_drag_pf=tax_drag_pf,
        tax_drag_pj=tax_drag_pj,
        capital_inicial=capital_inicial,
        rentabilidade_anual=rentabilidade_anual,
        horizonte_anos=horizonte_anos,
    )
