import pandas as pd
from pathlib import Path

def limpar_str(valor):
    """Garante que o valor é string tratada sem espaços nas pontas."""
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def classificar_cnpj(valor):
    v = limpar_str(valor)
    if v == "" or v in ["-", "N/A", "NA", "NULL", "0"]:
        return "vazio / nulo / traço"
    
    # Sem regex: separa dígitos de caracteres de máscara manualmente
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
    v = limpar_str(valor)
    if v == "" or v in ["-", "N/A", "NA", "NULL"]:
        return "vazio / nulo"
    
    if "-" in v and "T" in v:
        return "AAAA-MM-DDTHH:MM:SS"
    elif "-" in v:
        return "AAAA-MM-DD (com hífen)"
    elif "/" in v and ":" in v:
        return "DD/MM/AAAA com hora"
    elif "/" in v:
        return "DD/MM/AAAA (com barra)"
    elif "." in v:
        return "DD.MM.AAAA (com ponto)"
    elif v.isdigit() and len(v) == 8:
        return "AAAAMMDD (padrão compacto)"
    return "Outro formato de data"


def rodar_auditoria():
    print("=" * 60)
    print("INICIANDO AUDITORIA DE DADOS")
    print("=" * 60)
    
    # 1. Contagem de linhas de cada arquivo raw
    print("\n[1] CONTAGEM DE LINHAS DE CADA ARQUIVO RAW:")
    arquivos = ["compras", "itens", "resultados"]
    tabelas = {}
    
    for nome in arquivos:
        caminho = Path(f"data/raw/{nome}.csv")
        try:
            df = pd.read_csv(caminho, dtype=str, keep_default_na=False)
            tabelas[nome] = df
            print(f"  - {nome}.csv: {len(df)} linhas")
        except FileNotFoundError:
            print(f"  - {nome}.csv: Arquivo não encontrado no caminho data/raw/")
            tabelas[nome] = pd.DataFrame()

    compras = tabelas.get("compras")
    resultados = tabelas.get("resultados")
    
    if compras.empty:
        print("\nErro: O arquivo compras.csv é obrigatório para continuar a auditoria.")
        return

    # 2. Verificação de chaves repetidas (número de controle PNCP)
    print("\n[2] VERIFICAÇÃO DE CHAVES REPETIDAS EM COMPRAS:")
    if 'numero_controle_pncp' in compras.columns:
        duplicados = compras['numero_controle_pncp'].duplicated().sum()
        print(f"  - 'numero_controle_pncp' repetidos em compras.csv: {duplicados} registros")

    # 3. Contagem de formatos de CNPJ
    print("\n[3] FORMATOS E CONTAGEM DE CNPJ (cnpj_orgao):")
    print(compras['cnpj_orgao'].map(classificar_cnpj).value_counts())

    # 4. Contagem de formatos de Dinheiro
    if 'valor_total_homologado' in compras.columns:
        print("\n[4] FORMATOS E CONTAGEM DE DINHEIRO (valor_total_homologado):")
        print(compras['valor_total_homologado'].map(classificar_dinheiro).value_counts())

    # 5. Contagem de formatos de Data
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

    # 7. Verificação de acentos quebrados (Mojibake tipo 'Ã') sem regex
    print("\n[7] VERIFICAÇÃO DE ACENTOS QUEBRADOS (ex: 'Ã') POR COLUNA:")
    for nome_arq, df in tabelas.items():
        if df.empty:
            continue
        print(f"  - {nome_arq}.csv:")
        for col in df.columns:
            qtd_quebrados = 0
            for val in df[col]:
                v = str(val)
                if "Ã" in v:
                    qtd_quebrados += 1
            if qtd_quebrados > 0:
                print(f"      * Coluna '{col}': {qtd_quebrados} registros com acento quebrado")

    # 8. Verificação de cronologia estritamente sobre o resultados.csv
    print("\n[8] CRONOLOGIA: data_resultado x data_publicacao (Universo Total):")
    if not resultados.empty and 'data_resultado' in resultados.columns and not compras.empty:
        # Garante 1 para 1 no merge por PNCP
        compras_unicas = compras.drop_duplicates(subset=['numero_controle_pncp'])
        
        # Merge completo
        merged = resultados.merge(
            compras_unicas[['numero_controle_pncp', 'data_publicacao']], 
            on='numero_controle_pncp', 
            how='inner'
        )
        
        pub_dt = pd.to_datetime(merged['data_publicacao'], errors='coerce')
        res_dt = pd.to_datetime(merged['data_resultado'], errors='coerce')
        
        com_ambas = res_dt.notna() & pub_dt.notna()
        anteriores = (res_dt < pub_dt) & com_ambas
        
        
        print(f"  - Total de linhas cruzadas: {len(merged)}")
        print(f"  - Homologação ANTERIOR à publicação: {anteriores.sum()}")
 

if __name__ == "__main__":
    rodar_auditoria()