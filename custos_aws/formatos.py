"""Formatação pt-BR de valores em dólar."""

from __future__ import annotations

MESES = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
    7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez",
}


def usd(valor: float, casas: int = 2) -> str:
    """1234.5 -> 'US$ 1.234,50' (negativos com sinal antes do símbolo)."""
    sinal = "-" if valor < 0 else ""
    texto = f"{abs(valor):,.{casas}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"{sinal}US$ {texto}"


def usd_curto(valor: float) -> str:
    """Versão compacta para eixos e rótulos densos."""
    if abs(valor) >= 1000:
        return usd(valor, 0)
    return usd(valor, 2)


def pct(valor: float, casas: int = 1) -> str:
    if valor != valor:  # NaN
        return "—"
    return f"{valor * 100:+.{casas}f}%".replace(".", ",")


def mes_curto(ts) -> str:
    return f"{MESES[ts.month]}/{ts.year}"


# Os nomes do Cost Explorer são longos demais para eixo e legenda ("Amazon Elastic
# Compute Cloud - Compute" ocupa metade da largura útil). Aqui ficam as siglas de uso
# corrente; o que não estiver no mapa cai no desprefixamento genérico.
NOMES_CURTOS = {
    "Amazon Relational Database Service": "RDS",
    "Amazon Elastic Compute Cloud - Compute": "EC2 · computação",
    "EC2 - Other": "EC2 · outros",
    "Amazon Elastic Container Service": "ECS",
    "Amazon EC2 Container Registry (ECR)": "ECR",
    "Amazon Elastic Load Balancing": "Load Balancer",
    "Amazon Elastic MapReduce": "EMR",
    "Amazon Virtual Private Cloud": "VPC",
    "Amazon Simple Storage Service": "S3",
    "Amazon Simple Email Service": "SES",
    "Amazon Simple Notification Service": "SNS",
    "Amazon Simple Queue Service": "SQS",
    "AWS Database Migration Service": "DMS",
    "AWS Key Management Service": "KMS",
    "AmazonCloudWatch": "CloudWatch",
    "Tax": "Imposto",
}


def nome_curto(servico: str) -> str:
    if servico in NOMES_CURTOS:
        return NOMES_CURTOS[servico]
    for prefixo in ("Amazon ", "AWS "):
        if servico.startswith(prefixo):
            return servico[len(prefixo):]
    return servico


def dia_br(ts) -> str:
    return ts.strftime("%d/%m/%Y")
