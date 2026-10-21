<div align="center"> <h1>CyberReaper</h1> <p><b>Motor DAST Assíncrono para Testes de Segurança em Aplicações Web</b></p>

<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python" alt="Python"></a>
<a href="https://www.python-httpx.org/"><img src="https://img.shields.io/badge/Async-httpx-brightgreen?style=for-the-badge" alt="Async"></a>
<a href="https://owasp.org/www-project-top-ten/"><img src="https://img.shields.io/badge/OWASP-Top%2010-red?style=for-the-badge" alt="OWASP"></a>
<a href="#"><img src="https://img.shields.io/badge/False%20Positives-Validated-success?style=for-the-badge" alt="Zero FP"></a>
<a href="#"><img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="License"></a>
</div>
Sobre o Projeto

O CyberReaper é um motor DAST (Dynamic Application Security Testing) desenvolvido para identificar vulnerabilidades em aplicações web modernas. A ferramenta utiliza uma arquitetura assíncrona baseada nas bibliotecas asyncio e httpx, permitindo a execução de múltiplos testes simultâneos e otimizando o tempo de varredura. O sistema foi projetado para lidar com Single Page Applications (SPAs) e frameworks modernos, realizando a extração de endpoints diretamente de arquivos JavaScript.

O diferencial arquitetural do projeto é o seu motor de validação de falsos positivos. A ferramenta mitiga a geração de alertas incorretos através de análise contextual e diferencial. Para injeções SQL, o sistema compara a similaridade estrutural do HTML (difflib) entre payloads booleanos. Para XSS, valida se o código refletido é executável, ignorando caracteres HTML-encoded.
Principais Funcionalidades

    Arquitetura Assíncrona: Execução de testes paralelos para redução drástica no tempo de resposta do scan.

    Deep Crawler e Parser de JavaScript: Navegação estruturada em múltiplos níveis e extração de rotas de API ocultas em arquivos .js.

    Validação de Falsos Positivos (Zero FP):

        SQLi: Análise diferencial baseada em respostas booleanas.

        XSS: Validação de contexto e verificação de encoding.

        Command Injection: Detecção baseada em atraso de resposta (Time-Based).

    Evasão de WAF: Implementação de rotação de User-Agents e uso de payloads poliglotas.

    Relatório Executivo: Geração de documentação em formato HTML estruturado, contendo mapeamento OWASP e diretrizes de mitigação técnica.

Cobertura OWASP Top 10
Categoria OWASP	Testes Realizados pelo CyberReaper
A01:2021 - Broken Access Control	Falta de Token CSRF, Exposição de arquivos sensíveis (.env, .git), Open Redirect.
A02:2021 - Cryptographic Failures	Cookies sem flags Secure e HttpOnly.
A03:2021 - Injection	XSS Refletido, SQL Injection (Boolean), SSTI, Command Injection.
A05:2021 - Security Misconfiguration	Headers ausentes (CSP, HSTS), Métodos HTTP perigosos, CORS Misconfiguration.
A06:2021 - Vulnerable Components	Detecção de bibliotecas JavaScript desatualizadas (ex: jQuery antigo).
Instalação e Execução

Pré-requisitos: Python 3.9 ou superior e Git.

    Clone o repositório:

bash

git clone https://github.com/thaleshodan/cyberreaper.git
cd cyberreaper

    Instale as dependências do projeto:

bash

pip install -r requirements.txt

    Execute o motor de varredura:

bash

python cyberreaper.py

Insira a URL do alvo e a quantidade de threads (concorrência) no terminal para iniciar o processo. O relatório em HTML será gerado automaticamente no diretório local ao final da 
