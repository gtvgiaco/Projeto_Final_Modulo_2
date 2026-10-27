
/*Tema
Pergunta
1
Economia global do Poder Público
Qual é o percentual e o valor financeiro nominal economizado pelo governo (diferença entre valor estimado e valor homologado)?
*/


USE pncp_controladoria;

# opçao por usar  CTE para eliminar repeticao de codigo, melhor legibilidade e desempenho.
WITH totais AS(
	SELECT 
		SUM(CASE WHEN comparavel = 1 THEN valor_total_estimado ELSE 0 END) AS estimado_comparavel,# valor total estimado dos itens comparaveis
		SUM(CASE WHEN comparavel = 1 THEN valor_total_homologado ELSE 0 END) AS estimado_homologado  # valor total estimado dos itens comparaveis
	FROM fato_item_contratado
)
SELECT 
	estimado_comparavel, 
	estimado_homologado,
    (estimado_comparavel - estimado_homologado) AS economia_reais, # economia nominal
    ROUND(((estimado_comparavel - estimado_homologado) / NULLIF(estimado_comparavel, 0)) * 100, 2)AS economia_percentual # percentual de economia
FROM totais;
  

/*
2
Concentração e risco de fornecedores
Quem são os maiores fornecedores em volume financeiro e qual percentual do orçamento público está concentrado neles?
*/

SELECT 
	df.nome_fornecedor AS fornecedor,
    df.ni_fornecedor AS cnpj,
   SUM(f.valor_total_homologado) AS volume_financeiro,
   ROUND((SUM(f.valor_total_homologado) / NULLIF((
		SELECT SUM(valor_total_homologado)
        FROM fato_item_contratado
	), 0))* 100, 2) AS orcamento_percentual
FROM fato_item_contratado f
LEFT JOIN dim_fornecedor df ON f.sk_fornecedor = df.sk_fornecedor
GROUP BY df.nome_fornecedor, df.ni_fornecedor
ORDER BY volume_financeiro DESC
LIMIT 10;
    

/*
3
Eficácia por modalidade
Quais modalidades licitatórias trazem maior deságio/economia e quais concentram o maior volume de recursos?
*/

WITH comparacao_modalidades AS (
	SELECT
		dm.nome_modalidade AS modalidade,
        SUM(f.valor_total_estimado) AS total_estimado,
        SUM(f.valor_total_homologado) AS volume_recurso  # por modalidade        
FROM fato_item_contratado f
LEFT JOIN dim_modalidade dm ON f.sk_modalidade = dm.sk_modalidade
GROUP BY dm.nome_modalidade
)
SELECT
	modalidade,
    volume_recurso,
	(total_estimado - volume_recurso) AS valor_economia,
    ROUND(((total_estimado - volume_recurso) / NULLIF(total_estimado, 0)) * 100, 2) AS economia_percentual    
FROM comparacao_modalidades
ORDER BY valor_economia DESC;


/*
4
Tempo do ciclo de compras
Qual a duração média (em dias) entre o lançamento do edital e a sua homologação final, segmentada por órgão?
*/
#pergunta 4: agrupe pelo NOME do órgão, conte só itens com ciclo (COUNT(dias_ciclo)) e use HAVING para ficar com 5 ou mais; (6) perfil do gasto é coluna da própria fato (não precisa de JOIN). S
#ciclo = homologacao - publicacao

SELECT
	o.nome_orgao AS nome_orgao,
    COUNT(f.dias_ciclo) AS itens_com_ciclo, #quantidade de de itens com ciclo nao nulos em cada oergao
	ROUND(AVG(f.dias_ciclo), 2) AS duracao_media_dias
FROM fato_item_contratado f
LEFT JOIN dim_orgao o ON f.sk_orgao = o.sk_orgao
WHERE dias_ciclo IS NOT NULL
GROUP BY o.nome_orgao
HAVING COUNT(f.dias_ciclo) >= 5 # apenas orgaos com 5 ou mais itens com ciclo nao nulos
ORDER BY duracao_media_dias DESC; # ordenado do mais demorado para o menos demorado.

/*
5
Distribuição regional
Quais estados e regiões concentram as maiores despesas e quais apresentam os melhores indicadores de desconto?
*/

WITH estados_regioes AS (
	SELECT
		CASE
			WHEN dl.uf_sigla IN ('AC','AM', 'AP', 'PA', 'RO', 'RR', 'TO') THEN 'Norte'
            WHEN dl.uf_sigla IN ('AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE') THEN 'Nordeste'
            WHEN dl.uf_sigla IN ('DF', 'GO', 'MS', 'MT') THEN 'Centro-Oeste'
            WHEN dl.uf_sigla IN ('ES',  'MG', 'RJ', 'SP') THEN 'Sudeste'
            WHEN dl.uf_sigla IN ('PR','RS','SC') THEN 'Sul'
            ELSE 'Outros'
		END AS regiao,
		dl.uf_sigla AS estado,
        SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END) AS estimado_comparavel, #regra da economia, portanto comparavel = 1, responde a pergunta de melhores descontos (economia)
        SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_homologado ELSE 0 END) AS homologado_comparavel,  
        SUM(f.valor_total_homologado) AS volume_despesas_total # regra do volume, portanto comparaveis ou nao, responde a pergunta de maiores despesas total (volume).
    FROM fato_item_contratado f
    LEFT JOIN dim_localidade dl ON f.sk_localidade = dl.sk_localidade 
    GROUP BY dl.uf_sigla
)
SELECT
    regiao,
    estado,
    volume_despesas_total,  # responde a pergunta de maiores despesas total (volume).
	(estimado_comparavel - homologado_comparavel) AS valor_desconto, # responde a pergunta de melhores descontos (economia)
    ROUND(((estimado_comparavel - homologado_comparavel) / NULLIF(estimado_comparavel, 0)) * 100, 2) AS desconto_percentual
FROM estados_regioes
ORDER BY volume_despesas_total DESC;
            
            
            
/*
6
Perfil dos gastos
Como os recursos se distribuem entre bens, serviços e obras e engenharia? 
*/

SELECT
	f.perfil_gasto AS perfil,
    SUM(f.valor_total_homologado) AS valor_total, # soma do valor por perfil (group by)
    ROUND(
		(SUM(f.valor_total_homologado) / NULLIF(
		(SELECT SUM(valor_total_homologado)
        FROM fato_item_contratado),
        0)) * 100, 2) AS percentual
FROM fato_item_contratado f
GROUP BY f.perfil_gasto
ORDER BY valor_total DESC;



