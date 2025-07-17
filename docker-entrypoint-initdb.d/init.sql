-- Criação da tabela estado
CREATE TABLE IF NOT EXISTS estado (
    Cod_UF SERIAL PRIMARY KEY,
    UF VARCHAR(2) NOT NULL UNIQUE,
    Nome_Estado VARCHAR(50)
);

-- Criação da tabela servico
CREATE TABLE IF NOT EXISTS servico (
    Cod_Servico SERIAL PRIMARY KEY,
    Descricao_Servico VARCHAR(255) NOT NULL
);

-- Criação da tabela lote
CREATE TABLE IF NOT EXISTS lote (
    Cod_Lote SERIAL PRIMARY KEY,
    Descricao_Lote VARCHAR(255),
    Data_Criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criação da tabela pesquisa
CREATE TABLE IF NOT EXISTS pesquisa (
    Cod_Pesquisa SERIAL PRIMARY KEY,
    Cod_Cliente INT,
    Cod_Servico INT REFERENCES servico(Cod_Servico),
    Cod_UF INT REFERENCES estado(Cod_UF),
    Data_Entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Data_Conclusao TIMESTAMP,
    Nome VARCHAR(255),
    Nome_Corrigido VARCHAR(255),
    CPF VARCHAR(14), 
    RG VARCHAR(20),
    RG_Corrigido VARCHAR(20),
    Nascimento DATE,
    Mae VARCHAR(255),
    Mae_Corrigido VARCHAR(255),
    Anexo TEXT,
    Tipo INT, -- 0 para pessoa física, 1 para jurídica, etc.
    Cod_UF_Nascimento INT REFERENCES estado(Cod_UF),
    Cod_UF_RG INT REFERENCES estado(Cod_UF)
);

-- Criação da tabela lote_pesquisa (tabela de junção para N:M entre lote e pesquisa)
CREATE TABLE IF NOT EXISTS lote_pesquisa (
    Cod_Lote INT REFERENCES lote(Cod_Lote),
    Cod_Pesquisa INT REFERENCES pesquisa(Cod_Pesquisa),
    PRIMARY KEY (Cod_Lote, Cod_Pesquisa)
);

-- Criação da tabela pesquisa_spv
CREATE TABLE IF NOT EXISTS pesquisa_spv (
    Cod_Pesquisa_SPV SERIAL PRIMARY KEY, 
    Cod_Pesquisa INT REFERENCES pesquisa(Cod_Pesquisa),
    Cod_SPV INT, -- Assumindo que SPV é algum tipo de identificador, não uma FK ainda
    Cod_spv_computador INT,
    Cod_Spv_Tipo INT,
    Resultado INT,
    Cod_Funcionario INT,
    Filtro INT,
    Website_ID INT,
    Data_Registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para otimização de consultas comuns
CREATE INDEX IF NOT EXISTS idx_pesquisa_cpf ON pesquisa(CPF);
CREATE INDEX IF NOT EXISTS idx_pesquisa_rg ON pesquisa(RG);
CREATE INDEX IF NOT EXISTS idx_pesquisa_nome ON pesquisa(Nome);
CREATE INDEX IF NOT EXISTS idx_pesquisa_data_conclusao ON pesquisa(Data_Conclusao);
CREATE INDEX IF NOT EXISTS idx_pesquisa_spv_pesquisa ON pesquisa_spv(Cod_Pesquisa);
CREATE INDEX IF NOT EXISTS idx_pesquisa_spv_filtro ON pesquisa_spv(Filtro);

-- Exemplo de inserção de dados iniciais (opcional, para testes)
INSERT INTO estado (UF, Nome_Estado) VALUES ('SP', 'São Paulo') ON CONFLICT (UF) DO NOTHING;
INSERT INTO servico (Descricao_Servico) VALUES ('Consulta SPV') ON CONFLICT DO NOTHING;

-- Dados para uma consulta
-- Inserções para a tabela pesquisa
INSERT INTO pesquisa (Cod_Cliente, Cod_Servico, Cod_UF, Data_Entrada, Nome, CPF, RG, Nascimento, Mae, Anexo, Tipo, Cod_UF_Nascimento, Cod_UF_RG) VALUES
(101, 1, (SELECT Cod_UF FROM estado WHERE UF = 'SP'), CURRENT_TIMESTAMP, 'Joao Da Silva', '111.111.111-11', NULL, '1980-01-15', 'Maria Silva', NULL, 0, (SELECT Cod_UF FROM estado WHERE UF = 'SP'), NULL) ON CONFLICT (CPF) DO NOTHING;

INSERT INTO pesquisa (Cod_Cliente, Cod_Servico, Cod_UF, Data_Entrada, Nome, CPF, RG, Nascimento, Mae, Anexo, Tipo, Cod_UF_Nascimento, Cod_UF_RG) VALUES
(102, 1, (SELECT Cod_UF FROM estado WHERE UF = 'SP'), CURRENT_TIMESTAMP, 'Maria Oliveira', '222.222.222-22', '123456789', '1990-05-20', 'Ana Oliveira', NULL, 0, (SELECT Cod_UF FROM estado WHERE UF = 'SP'), (SELECT Cod_UF FROM estado WHERE UF = 'SP')) ON CONFLICT (CPF) DO NOTHING;

INSERT INTO pesquisa (Cod_Cliente, Cod_Servico, Cod_UF, Data_Entrada, Nome, CPF, RG, Nascimento, Mae, Anexo, Tipo, Cod_UF_Nascimento, Cod_UF_RG) VALUES
(103, 1, (SELECT Cod_UF FROM estado WHERE UF = 'SP'), CURRENT_TIMESTAMP, 'Jose Santos', '333.333.333-33', NULL, '1975-11-10', 'Paula Santos', NULL, 0, (SELECT Cod_UF FROM estado WHERE UF = 'SP'), NULL) ON CONFLICT (CPF) DO NOTHING;


INSERT INTO pesquisa_spv (Cod_Pesquisa, Cod_SPV, Cod_spv_computador, Cod_Spv_Tipo, Resultado, Cod_Funcionario, filtro, website_id, Data_Registro) VALUES
((SELECT Cod_Pesquisa FROM pesquisa WHERE CPF = '111.111.111-11'), 1, 36, NULL, NULL, -1, 0, 1, CURRENT_TIMESTAMP) ON CONFLICT DO NOTHING;

INSERT INTO pesquisa_spv (Cod_Pesquisa, Cod_SPV, Cod_spv_computador, Cod_Spv_Tipo, Resultado, Cod_Funcionario, filtro, website_id, Data_Registro) VALUES
((SELECT Cod_Pesquisa FROM pesquisa WHERE CPF = '222.222.222-22'), 1, 36, NULL, NULL, -1, 1, 1, CURRENT_TIMESTAMP) ON CONFLICT DO NOTHING;