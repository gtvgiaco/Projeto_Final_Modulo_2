
# Projeto Final - Análise de Dados - Módulo 2 (SCTEC)

## Desenvolvimento de esteira analítica para analisar dados do Portal Nacional de Contratações Públicas (PNCP)

#### Aluno: Gustavo Giacomini

## 1. Contexto do Problema

Atuarei como Analista de Dados contratado por uma consultoria de inteligência governamental que atende órgãos de controle e transparência pública.

Recentemente, a Controladoria identificou gargalos operacionais severos nas compras e contratações públicas federais: 

- indícios de sobrepreço em itens homologados, 
- concentração atípica de contratos em determinados grupos econômicos, 
- morosidade excessiva entre a publicação de editais e o fechamento dos certames, 
- baixa adesão competitiva em certas modalidades.
- sistemas legados sem travas rígidas de validação na ponta, resultando em dados com diversas anomalias: 
	- identificadores corrompidos,
	- campos monetários preenchidos em texto livre,
	- inconsistências lógicas de cronograma,
	- formatos de data despadronizados.

A liderança governamental precisa de clareza para a tomada de decisão estratégica e auditoria contínua, mas hoje não confia nos relatórios gerados a partir desses dados brutos.

### Os Dados

A base oficial é o Portal Nacional de Contratações Públicas (PNCP) / Dados Abertos do Governo Federal (dados.gov.br),  com recorte de janeiro/2025 a setembro/2026 (decidi fazer um recorte maior, visto que os arquivos possuem homologações em 2026). A extração do portal ou da API oficial (https://pncp.gov.br/api/consulta/) já foi feita pela professor, e não precisamos baixar nada.

Os dados de cabeçalho dos certames (órgãos, datas, modalidades) com os dados de itens licitados (valores unitários estimados e homologados, quantidades e descrições).

### Estrutura do repositório:


## 2. Tecnologias utilizadas

- Python 
- MySQL
- Power Bi
- Git Hub/Git Hub Desktop

## 3. Instruções de execução: Reproduzindo o pipeline do zero.

Caso queira clonar e reproduzir este pipeline de dados e relatórios:


### 3.1 Clonar o repositório:

git clone [https://github.com/gtvgiaco/Projeto_Final_Modulo_2.git](https://github.com/gtvgiaco/Projeto_Final_Modulo_2.git)
cd Projeto_Final_Modulo_2

### 3.2 Configurar o ambiente virtual

- python -m venv venv
- source venv/bin/activate  # No Windows: venv\Scripts\activate
- pip install -r requirements.txt

### 3.3 Execução do pipeline (ETL)

Execute os scripts de extração e tratamento localizados na pasta /src:

python -m src.limpeza            # tratamento dos problemas nos dados

python -m src.montar_tabelas     # montagem da tabela fato e das 4 dimensões em data/processed/

python -m src.carregar     		 # criação do banco de dados e carregamento das tabelas no MySQL.

### 3.4 Acesso às perguntas de negócio:

- Abra o arquivo sql/02_perguntas.sql no MySQL e rode os selects, um por vez, no banco pncp_controladoria.

### 3.5 Abertura do Painel Power BI:
- Instale o conector no MySQL: MySQL Connector/NET 8.

- Abra o arquivo .pbix em powerbi/dashboard no Power BI Desktop.

- Apontar a conexão de dados para a sua instância local do banco de dados MySQL.

- Clique em Atualizar para carregar o modelo dimensional finalizado.


## 4. Sprints do projeto

O projeto foi dividido em 5 sripnts, conforme a imagem abaixo.

![alt text](sprints.png)

## 5. Diagnóstico Inicial

Para responder as perguntas do item 7.4 do enunciado, usamos o auditoria.py . Abaixo as perguntas de diagnóstico inicial dos arquivos brutos.

- Quantas linhas tem cada arquivo? Há numero_controle_pncp repetido em compras.csv?

![alt text](image-5.png)

- Que formatos de dinheiro, de data e de CNPJ aparecem? Quais colunas têm N/A, -, 0, vazio?

![alt text](image-6.png)

![alt text](image-7.png)

- Existe texto com acento quebrado (Ã§, Ã£)? Em quais colunas?

![alt text](image-8.png)

- Existe data_resultado anterior a data_publicacao?

![alt text](image-10.png)


## 6. Limpeza dos arquivos brutos

O limpeza.py é responsável por normalizar e limpar os dados brutos. Cada funcao resolve UM problema  (CNPJ com mascara, "R$ 1.234,56", datas em varios formatos...).

| Função | Assinatura / Parâmetros | Descrição |
| :--- | :--- | :--- |
| **`remover_invisiveis`** | `(texto)` | Apaga caracteres invisíveis de largura zero vindos de sistemas antigos. |
| **`consertar_acento`** | `(texto)` | Corrige acentos corrompidos (ex: UTF-8 lido incorretamente como Latin-1). |
| **`tirar_espacos`** | `(texto)` | Remove espaços das pontas e normaliza espaços internos repetidos. |
| **`eh_nulo`** | `(texto, zero_eh_nulo=True)` | Verifica se o texto significa "sem valor" (`N/A`, `NULL`, vazios, etc.). O zero pode ser nulo se especificado. |
| **`limpar_texto`** | `(texto, zero_eh_nulo=True)` | Aplica limpeza geral (invisíveis, acentos, espaços) e retorna `None` se for um nulo disfarçado. |
| **`padronizar_nome`** | `(texto)` | Converte o texto para MAIÚSCULAS e padroniza hífens e espaçamentos (ex: órgãos, fornecedores). |
| **`limpar_documento`** | `(texto, tipo_pessoa=None)` | Isola apenas os dígitos de CNPJs ou CPFs, restaurando zeros à esquerda (`zfill`) com base no tipo (`PJ`, `PF`, `PE`). |
| **`converter_numero`** | `(texto)` | Converte strings complexas de dinheiro ou números (com `R$`, negativos, pontos/vírgulas trocados) em `float`. |
| **`converter_data`** | `(texto)` | Interpreta datas em múltiplos formatos e converte para `datetime.date`, validando se o ano está entre 2000 e 2030. |

Para rodar utilize python -m src.limpeza

## 7. Montagem das tabelas

Consome os arquivos CSV brutos, aplica regras rigorosas de limpeza, validação e negócio, e gera o modelo dimensional composto por uma tabela fato (`fato_item_contratado`) e quatro dimensões (`dim_orgao`, `dim_fornecedor`, `dim_modalidade` e `dim_localidade`).

Este script em Python faz parte da etapa de transformação de dados (`ETL` - Extract, Transform, Load). Ele consome os arquivos CSV brutos (dados do PNCP - Portal Nacional de Contratações Públicas), aplica regras rigorosas de limpeza, validação e negócio, e gera o modelo dimensional composto por uma tabela fato (`fato_item_contratado`) e quatro dimensões (`dim_orgao`, `dim_fornecedor`, `dim_modalidade` e `dim_localidade`).

O script executa o processamento em 10 etapas sequenciais:

1. **Limpeza dos Arquivos Brutos:** Utiliza as funções do módulo `limpeza.py` para normalizar textos, corrigir documentos (CPFs/CNPJs com zeros à esquerda), interpretar valores numéricos e converter datas.
2. **Filtragem de Vencedores por Item:** Remove itens cancelados e seleciona a melhor classificação (vencedor) para cada item de compra.
3. **Cruzamento de Dados (Merge):** Realiza a junção entre compras, itens e resultados (`inner join`), garantindo que apenas itens com resultados válidos processem a etapa seguinte.
4. **Tratamento de Valores:** Ajusta quantidades homologadas e recalcula os valores totais estimados e homologados.
5. **Rejeição de Itens:** Descarta registros inconsistentes (como orçamentos sigilosos, quantidades ou valores inválidos/zerados, e valores acima de limites aceitáveis).
6. **Cálculo de Comparabilidade e Economia:** Identifica quais itens são comparáveis (excluindo credenciamentos e variações extremas fora da faixa de 0.1 a 10) e calcula a economia gerada.
7. **Análise Cronológica (Ciclo):** Valida as datas de homologação em relação à publicação e calcula o tempo de ciclo (em dias) das contratações.
8. **Perfil do Gasto:** Classifica os itens de acordo com a natureza da despesa em **Bens**, **Serviços** ou **Obras e engenharia** (com base em palavras-chave e tipo de fornecimento).
9. **Geração do Modelo Dimensional:** Cria as tabelas de dimensão com chaves substitutas (`sk_`) e substitui as chaves naturais na tabela fato.
10. **Persistência e Prova Real:** Salva todas as tabelas processadas em `data/processed/` e imprime métricas comparativas para validação com o gabarito oficial (Anexo 8).

Para rodar utilize python -m src.montar_tabelas

## 8. Modelagem dimensional e carga (MySQL)

O 01_criar_banco.sql cria a estrutura do banco de dados relacional `pncp_controladoria`, implementando o **modelo dimensional (Star Schema)** para o armazenamento e controle dos dados processados de contratações públicas.

Garante a integridade referencial, define chaves primárias e substitutas (`sk_`), estabelece restrições de unicidade (`UNIQUE`), restrições de verificação (`CHECK`) e inclui registros padrão (`-1`) para o tratamento de chaves órfãs ou não informadas.

Etapas:

1. **Criação do Banco de Dados:** Inicializa o banco `pncp_controladoria` e desativa temporariamente as checagens de chave estrangeira (`FOREIGN_KEY_CHECKS`) para permitir a limpeza segura de tabelas existentes.
2. **Remoção de Tabelas Antigas:** Executa um `DROP TABLE IF EXISTS` seguro em ordem reversa de dependência para evitar conflitos.
3. **Criação das Dimensões:**
   * `dim_orgao`: Contém os dados dos órgãos públicos contratantes.
   * `dim_fornecedor`: Contém os dados dos fornecedores (Pessoa Jurídica, Física ou Estrangeira) e seus portes.
   * `dim_modalidade`: Armazena as modalidades de contratação.
   * `dim_localidade`: Armazena as informações geográficas (UF, nome do estado e região do país).
4. **Criação da Tabela Fato:**
   * `fato_item_contratado`: Armazena os itens contratados associados às quatro dimensões, contendo métricas quantitativas, financeiras, de economia, comparabilidade e cronologia (dias de ciclo).
5. **Registros de Fallback (`-1`):** Insere registros coringa (`-1`) em todas as dimensões para garantir a integridade de dados caso algum registro da fato não possua correspondência direta.


**Modelo Star Schema
**
![alt text](star_schema-1.png)

## 9. Power BI

O painel foi estruturado em **6 páginas temáticas**, respondendo a perguntas estratégicas de controle e transparência dos gastos públicos, amparado por uma **tabela de medidas dedicada** e regras estritas de DAX com uso de `VAR`/`RETURN`, `CALCULATE`, `DIVIDE` e funções iteradoras.

Todas as medidas obrigatórias foram centralizadas em uma tabela dedicada (chamada `_Medidas`) e organizadas em **pastas de exibição** correspondentes a cada pergunta/página do dashboard.

### Tabela de Resumo das 15 Medidas Obrigatórias

| Pasta  |  Nome  | O que calcula |
| :--- | :---: | :--- | :--- |
| **P1 Economia** |  `valor_estimado_comparavel` | Soma do valor estimado só dos itens comparáveis. |
| **P1 Economia** |  `volume_homologado` | Soma do valor total homologado de todos os itens. |
| **P1 Economia** |  `economia(R$)` | Estimado comparável − homologado dos itens comparáveis. |
| **P1 Economia** |  `economia(%)` | Economia (R$) ÷ Valor Estimado Comparável. |
| **P1 Economia** |  `%_itens_comparaveis` | Itens comparáveis ÷ total de itens. |
| **P2 Fornecedores** |  `participação_fornecedor(%)` | Volume do fornecedor ÷ volume total (ignorando filtros). |
| **P2 Fornecedores** |  `ranking_fornecedor` | Posição do fornecedor por volume (1º, 2º, 3º…). |
| **P2 Fornecedores** |  `top_10_fornecedores%` | Volume dos 10 maiores fornecedores ÷ volume total. |
| **P3 Modalidades** |  `participaçã_volume(%)` | Volume da linha atual ÷ volume total. |
| **P3 Modalidades** |  `desagio_vs_media_geral` | Economia % da linha atual − Economia % geral (em pontos percentuais). |
| **P4 Ciclo** |  `ciclo_medio(dias)` | Média dos dias entre publicação e homologação (ignora vazios). |
| **P4 Ciclo** |  `ciclo_maximo(dias)` | Maior ciclo observado. |
| **P4 Ciclo** |  `iens_sem_ciclo` | Total de itens − itens com ciclo. |
| **P5 Regional** | `qtd_unidades_compradoras` | Número de CNPJs de órgão distintos. |
| **P6 Perfil** | `ticket_medio_por_item(R$)` | Valor médio por item vendido. |

## DASHBOARD

