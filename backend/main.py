import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from calculator import calcular_comparativo

app = FastAPI(
    title="ArbiTrib - Calculadora Tributária PF vs PJ",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


class CalculadoraInput(BaseModel):
    capital_inicial: float = Field(1_000_000, gt=0, description="Capital inicial (R$)")
    rentabilidade_anual: float = Field(
        0.10, gt=0, lt=1, description="Taxa de retorno anual, ex: 0.10 = 10%"
    )
    horizonte_anos: int = Field(10, ge=1, le=50, description="Horizonte em anos")
    ir_pf_rate: float = Field(
        0.15,
        ge=0.0,
        le=0.225,
        description="Alíquota IR PF (0% se isento, 15%-22.5% se tributado)",
    )
    ir_pj_rate: float = Field(
        0.34, ge=0.0, le=0.50, description="Alíquota IRPJ+CSLL, padrão 34%"
    )
    overhead_anual: float = Field(
        70_000, ge=0, description="Custos operacionais anuais da holding (R$)"
    )
    taxa_distribuicao: float = Field(
        0.50,
        ge=0,
        le=1,
        description="% do lucro distribuído como dividendos anualmente",
    )
    usar_deferimento: bool = Field(
        False,
        description="PJ com diferimento tributário (compõe sobre bruto, IR só no final)",
    )
    taxa_dividendos: float = Field(
        0.10, ge=0, le=0.30, description="Alíquota sobre dividendos (Lei 14.754/2023)"
    )
    itcmd_max_rate: float = Field(
        0.08,
        ge=0,
        le=0.20,
        description="Alíquota ITCMD máxima (8% atual, até 16% reforma)",
    )
    desconto_quota_holding: float = Field(
        0.20, ge=0, le=0.50, description="Desconto na base ITCMD das quotas da holding"
    )
    isento_pf: bool = Field(
        False, description="Aplicação isenta de IR para PF (LCI/LCA/CRI/CRA)"
    )
    spread_pj: float = Field(
        0.0,
        ge=0,
        le=0.05,
        description="Spread da corretora para PJ (ex: título público). 0.005 = 0,5%",
    )
    ibs_cbs_rate: float = Field(
        0.0,
        ge=0,
        le=0.30,
        description="Alíquota IBS+CBS sobre receita bruta da PJ (reforma tributária)",
    )


def _fmt_ano(a) -> dict:
    return {
        "ano": a.ano,
        "saldo_inicial": round(a.saldo_inicial, 2),
        "retorno_bruto": round(a.retorno_bruto, 2),
        "impostos_ganhos": round(a.impostos_ganhos, 2),
        "custos_operacionais": round(a.custos_operacionais, 2),
        "custos_ibs_cbs": round(a.custos_ibs_cbs, 2),
        "distribuicao_bruta": round(a.distribuicao_bruta, 2),
        "imposto_distribuicao": round(a.imposto_distribuicao, 2),
        "reinvestido": round(a.reinvestido, 2),
        "saldo_final": round(a.saldo_final, 2),
        "patrimonio_acumulado": round(a.patrimonio_acumulado, 2),
    }


@app.post("/api/calcular")
def calcular(data: CalculadoraInput):
    r = calcular_comparativo(
        capital_inicial=data.capital_inicial,
        rentabilidade_anual=data.rentabilidade_anual,
        horizonte_anos=data.horizonte_anos,
        ir_pf_rate=data.ir_pf_rate,
        ir_pj_rate=data.ir_pj_rate,
        overhead_anual=data.overhead_anual,
        taxa_distribuicao=data.taxa_distribuicao,
        usar_deferimento=data.usar_deferimento,
        taxa_dividendos=data.taxa_dividendos,
        itcmd_max_rate=data.itcmd_max_rate,
        desconto_quota_holding=data.desconto_quota_holding,
        isento_pf=data.isento_pf,
        spread_pj=data.spread_pj,
        ibs_cbs_rate=data.ibs_cbs_rate,
    )

    return {
        "vencedor": r.vencedor,
        "vfl_pf": round(r.pf.vfl, 2),
        "vfl_pj": round(r.pj.vfl, 2),
        "nome_pj": r.pj.nome,
        "diferenca_absoluta": round(r.diferenca_absoluta, 2),
        "diferenca_percentual": round(r.diferenca_percentual, 2),
        "tax_drag_pf": round(r.tax_drag_pf, 2),
        "tax_drag_pj": round(r.tax_drag_pj, 2),
        "total_impostos_pf": round(r.pf.total_impostos, 2),
        "total_impostos_pj": round(r.pj.total_impostos, 2),
        "saldo_final_pf": round(r.pf.saldo_final, 2),
        "saldo_final_pj": round(r.pj.saldo_final, 2),
        "total_distribuido_pf": round(r.pf.total_distribuido_liquido, 2),
        "total_distribuido_pj": round(r.pj.total_distribuido_liquido, 2),
        "anos_pf": [_fmt_ano(a) for a in r.pf.anos],
        "anos_pj": [_fmt_ano(a) for a in r.pj.anos],
        "itcmd": {
            "base_pf": round(r.itcmd.base_pf, 2),
            "base_pj": round(r.itcmd.base_pj, 2),
            "itcmd_pf": round(r.itcmd.itcmd_pf, 2),
            "itcmd_pj": round(r.itcmd.itcmd_pj, 2),
            "economia": round(r.itcmd.economia, 2),
            "aliquota_efetiva_pf": round(r.itcmd.aliquota_efetiva_pf, 2),
            "aliquota_efetiva_pj": round(r.itcmd.aliquota_efetiva_pj, 2),
            "vfl_pos_sucessao_pf": round(r.itcmd.vfl_pos_sucessao_pf, 2),
            "vfl_pos_sucessao_pj": round(r.itcmd.vfl_pos_sucessao_pj, 2),
            "vencedor_sucessao": r.itcmd.vencedor_sucessao,
            "diferenca_sucessao": round(r.itcmd.diferenca_sucessao, 2),
        },
        "parametros": {
            "capital_inicial": data.capital_inicial,
            "rentabilidade_anual": data.rentabilidade_anual,
            "horizonte_anos": data.horizonte_anos,
            "ir_pf_rate": data.ir_pf_rate,
            "ir_pj_rate": data.ir_pj_rate,
            "overhead_anual": data.overhead_anual,
            "taxa_distribuicao": data.taxa_distribuicao,
            "usar_deferimento": data.usar_deferimento,
            "taxa_dividendos": data.taxa_dividendos,
            "itcmd_max_rate": data.itcmd_max_rate,
            "desconto_quota_holding": data.desconto_quota_holding,
            "isento_pf": data.isento_pf,
            "spread_pj": data.spread_pj,
            "ibs_cbs_rate": data.ibs_cbs_rate,
        },
    }


# Serve frontend
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
