from pathlib import Path
import pandas as pd
import config
import limpeza


def limpar_str(valor):
    """Garante que o valor é string tratada sem espaços nas pontas."""
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def classificar_cnpj(valor):
    v = limpar_str(valor)
    if v == "" or v in ["-", "N/A", "NA", "NULL", "0"]:
        return "vazio / nulo / traço"
    
    apenas_digitos = ""
    tem_mascara = False
    for char in v:
        if char.isdigit():
            apenas_digitos += char
        else:
            tem_mascara = True
            
    tamanho = len(apenas_digitos)
    if tamanho == 14:
        return "CNPJ com máscara" if tem_mascara else "CNPJ apenas números"
    elif tamanho < 14:
        return "CNPJ incompleto (< 14 dígitos)"
    else:
        return "CNPJ com dígitos demais (> 14 dígitos)"


def classificar_dinheiro(valor):
    v = limpar_str(valor).replace("R$", "").strip()
    if v == "" or v in ["-", "N/A", "NA", "NULL"]:
        return "vazio / nulo"
    
    tem_ponto = "." in v
    tem_virgula = "," in v
    
    if not tem_ponto and not tem_virgula:
        return "Apenas dígitos (inteiro)"
    elif tem_ponto and not tem_virgula:
        return "Contém ponto (ex: 1234.56)"
    elif not tem_ponto and tem_virgula:
        return "Contém vírgula (ex: 1234,56)"
    elif tem_ponto and tem_virgula:
        return "Contém ponto e vírgula (formato misto/milhar)"
    return "Outro formato"


def classificar_data(valor):
    t = limpar_str(valor)
    if not t or t in ["-", "N/A", "NA", "NULL"]:
        return "vazio / nulo"
    
    # Valida usando o conversor seguro do módulo de limpeza
    if limpeza.converter_data(t) is None:
        return "Data inválida ou fora do intervalo"
    
    # Identificação exata dos formatos exibidos no padrão desejado
    if "-" in t and "T" in t:
        return "AAAA-MM-DDTHH:MM:SS"
    elif "/" in t and ":" in t:
        return "DD/MM/AAAA com hora"
    elif "/" in t:
        return "DD/MM/AAAA (com barra)"
    elif "-" in t:
        return "AAAA-MM-DD (com hífen)"
    elif "." in t:
        return "DD.MM.AAAA (com ponto)"
    elif t.isdigit() and len(t) == 8:
        return "AAAAMMDD (padrão compacto)"
    return "Outro formato de data"

def secao_cronologia(compras, resultados):
    print("\n[8] CRONOLOGIA: data_resultado x data_publicacao (Universo Total):")
    
    # Mapeia a publicação utilizando a função oficial de conversão do colega
    publicacao = (
        compras.drop_duplicates(subset=["numero_controle_pncp"])
        .set_index("numero_controle_pncp")["data_publicacao"]
        .map(limpeza.converter_data)
    )
    
    r = resultados.copy()
    r["pub"] = pd.to_datetime(r["numero_controle_pncp"].map(publicacao))
    r["res"] = pd.to_datetime(r["data_resultado"].map(limpeza.converter_data))
    
    if "data_cancelamento" in r.columns:
        cancelado = r["data_cancelamento"].map(limpar_str) != ""
    else:
        cancelado = pd.Series([False] * len(r))
    
    for nome, parte in [("todos os resultados", r), ("so resultados nao cancelados", r[~cancelado])]:
        sem_data = parte["res"].isna() | parte["pub"].isna()
        print(f"    {nome} ({len(parte)}):")
        print(f"       sem data valida (resultado ou publicacao): {sem_data.sum()}")
        print(f"       homologacao ANTERIOR a publicacao (impossivel): {(parte['res'] < parte['pub']).sum()}")
        print(f"       homologacao no mesmo dia da publicacao (valida, ciclo 0): {(parte['res'] == parte['pub']).sum()}")
        print(f"       homologacao posterior a publicacao: {(parte['res'] > parte['pub']).sum()}")


def rodar_auditoria():
    print("=" * 60)
    print("INICIANDO AUDITORIA DE DADOS")
    print("=" * 60)
    
    # 1. Carregamento dos dados
    print("\n[1] CONTAGEM DE LINHAS DE CADA ARQUIVO RAW:")
    tabelas = {}
    for nome in ["compras", "itens", "resultados"]:
        caminho = Path(f"data/raw/{nome}.csv")
        try:
            df = pd.read_csv(caminho, dtype=str, keep_default_na=False)
            tabelas[nome] = df
            print(f"  - {nome}.csv: {len(df)} linhas")
        except FileNotFoundError:
            print(f"  - {nome}.csv: Arquivo não encontrado")
            tabelas[nome] = pd.DataFrame()

    compras = tabelas.get("compras")
    resultados = tabelas.get("resultados")
    
    if compras.empty:
        print("\nErro: O arquivo compras.csv é obrigatório.")
        return

    # 2. Chaves repetidas
    print("\n[2] VERIFICAÇÃO DE CHAVES REPETIDAS EM COMPRAS:")
    if 'numero_controle_pncp' in compras.columns:
        duplicados = compras['numero_controle_pncp'].duplicated().sum()
        print(f"  - 'numero_controle_pncp' repetidos: {duplicados} registros")

    # 3. CNPJ
    print("\n[3] FORMATOS E CONTAGEM DE CNPJ (cnpj_orgao):")
    print(compras['cnpj_orgao'].map(classificar_cnpj).value_counts())

    # 4. Dinheiro
    if 'valor_total_homologado' in compras.columns:
        print("\n[4] FORMATOS E CONTAGEM DE DINHEIRO (valor_total_homologado):")
        print(compras['valor_total_homologado'].map(classificar_dinheiro).value_counts())

    # 5. Datas
    if 'data_publicacao' in compras.columns:
        print("\n[5] FORMATOS E CONTAGEM DE DATAS (data_publicacao):")
        print(compras['data_publicacao'].map(classificar_data).value_counts())

    # 6. Mapeamento de colunas com vazios, traços, N/A e zeros
    print("\n[6] COLUNAS COM NULOS, TRAÇOS (-), ZEROS (0) OU VAZIOS (em compras):")
    for col in compras.columns:
        contagem = {"vazio": 0, "traço (-)": 0, "N/A / NULL": 0, "zero (0)": 0}
        for val in compras[col]:
            v = limpar_str(val)
            if v == "":
                contagem["vazio"] += 1
            elif v == "-":
                contagem["traço (-)"] += 1
            elif v.upper() in ["N/A", "NA", "NULL"]:
                contagem["N/A / NULL"] += 1
            elif v == "0":
                contagem["zero (0)"] += 1
        total_anomalias = sum(contagem.values())
        if total_anomalias > 0:
            print(f"  - Coluna '{col}': {contagem}")


    # 7. Acentos quebrados (Mojibake)
    print("\n[7] VERIFICAÇÃO DE ACENTOS QUEBRADOS (ex: 'Ã') POR COLUNA:")
    for nome_arq, df in tabelas.items():
        if df.empty:
            continue
        for col in df.columns:
            qtd = sum(1 for val in df[col] if "Ã" in str(val))
            if qtd > 0:
                print(f"  - {nome_arq}.csv -> Coluna '{col}': {qtd} registros com acento quebrado")

    # 8. Cronologia oficial
    secao_cronologia(compras, resultados)


if __name__ == "__main__":
    rodar_auditoria()