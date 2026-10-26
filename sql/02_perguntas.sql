
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
        SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END) AS estimado_comparavel,
        SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_homologado ELSE 0 END) AS homologado_comparavel,
        SUM(f.valor_total_homologado) AS volume_recurso  # por modalidade        
FROM fato_item_contratado f
LEFT JOIN dim_modalidade dm ON f.sk_modalidade = dm.sk_modalidade
GROUP BY dm.nome_modalidade
)
SELECT
	modalidade,
	(estimado_comparavel - homologado_comparavel) AS valor_economia,
    volume_recurso
FROM comparacao_modalidades
ORDER BY valor_economia DESC;


/*
4
Tempo do ciclo de compras
Qual a duração média (em dias) entre o lançamento do edital e a sua homologação final, segmentada por órgão?



5
Distribuição regional
Quais estados e regiões concentram as maiores despesas e quais apresentam os melhores indicadores de desconto?


6
Perfil dos gastos
Como os recursos se distribuem entre bens, serviços e obras e engenharia? 
*/


