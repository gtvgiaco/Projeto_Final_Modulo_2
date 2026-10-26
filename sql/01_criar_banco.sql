CREATE DATABASE IF NOT EXISTS pncp_controladoria;

USE pncp_controladoria;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS fato_item_contratado;
DROP TABLE IF EXISTS dim_orgao;
DROP TABLE IF EXISTS dim_fornecedor;
DROP TABLE IF EXISTS dim_modalidade;
DROP TABLE IF EXISTS dim_localidade;

CREATE TABLE dim_orgao (
	sk_orgao INT AUTO_INCREMENT PRIMARY KEY,
    cnpj_orgao VARCHAR(14) NOT NULL UNIQUE,
    nome_orgao VARCHAR(255),
    poder VARCHAR(20)
)ENGINE=InnoDB;

CREATE TABLE dim_fornecedor (
	sk_fornecedor INT  AUTO_INCREMENT PRIMARY KEY,
    ni_fornecedor VARCHAR(20) NOT NULL UNIQUE,
    nome_fornecedor VARCHAR(255),
    tipo_pessoa VARCHAR(2),
    porte VARCHAR(20)
)ENGINE=InnoDB;

CREATE TABLE dim_modalidade(
	sk_modalidade INT  AUTO_INCREMENT PRIMARY KEY,
    modalidade_id INT NOT NULL UNIQUE,
    nome_modalidade VARCHAR(30)
)ENGINE=InnoDB;
    
CREATE TABLE dim_localidade(
	sk_localidade INT AUTO_INCREMENT PRIMARY KEY,
    uf_sigla VARCHAR(2) NOT NULL UNIQUE,
    uf_nome VARCHAR(20),
    regiao VARCHAR(20)
)ENGINE=InnoDB;
	
CREATE TABLE fato_item_contratado (
    sk_fato INT AUTO_INCREMENT PRIMARY KEY,
    numero_controle_pncp VARCHAR(50) NOT NULL,
    numero_item INT NOT NULL,
    sk_orgao INT,
    sk_fornecedor INT,
    sk_modalidade INT,
    sk_localidade INT,
    data_publicacao DATE NOT NULL,
    data_homologacao DATE NULL,  #NULL se a regra 7 anula a homologacao
    descricao_item TEXT,
    perfil_gasto VARCHAR(50) NOT NULL,
    quantidade DECIMAL(18,4) NOT NULL CHECK (quantidade > 0), #a fato não aceita quantidade ≤ 0 nem valores negativos 
    valor_unitario_estimado DECIMAL(18,4) NOT NULL CHECK (valor_unitario_estimado >=0),
    valor_total_estimado DECIMAL(18,2) NOT NULL CHECK (valor_total_estimado >=0),
    valor_unitario_homologado DECIMAL(18,4) NOT NULL CHECK (valor_unitario_homologado >=0),
    valor_total_homologado DECIMAL(18,2) NOT NULL CHECK (valor_total_homologado >= 0),
    comparavel TINYINT,
    economia_valor DECIMAL(18,2) NULL, #NULL nos itens nao comparaveis 
    dias_ciclo INT NULL, #NULL se a regra 7 anula a homologacao
    UNIQUE KEY uk_pncp_item (numero_controle_pncp, numero_item),
    FOREIGN KEY (sk_orgao) REFERENCES dim_orgao(sk_orgao),
    FOREIGN KEY (sk_fornecedor) REFERENCES dim_fornecedor(sk_fornecedor),
    FOREIGN KEY (sk_modalidade) REFERENCES dim_modalidade(sk_modalidade),
    FOREIGN KEY (sk_localidade) REFERENCES dim_localidade(sk_localidade)
);

INSERT INTO dim_orgao (sk_orgao, cnpj_orgao, nome_orgao, poder) 
VALUES (-1, '00000000000000', 'Não informado', 'Não informado' );

INSERT INTO dim_fornecedor (sk_fornecedor, ni_fornecedor, nome_fornecedor, tipo_pessoa, porte) 
VALUES (-1, '00000000000000', 'Não informado', 'NI', 'Não informado');

INSERT INTO dim_modalidade (sk_modalidade, modalidade_id, nome_modalidade) 
VALUES (-1, -1, 'Não informado');

INSERT INTO dim_localidade (sk_localidade, uf_sigla, uf_nome, regiao) 
VALUES (-1, 'NI', 'Não informado', 'Não informado');	 



SET FOREIGN_KEY_CHECKS = 1;