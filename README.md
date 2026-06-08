# DDNS Finder - Intelbras

Ferramenta em Python para enumerar subdomínios válidos no domínio `ddns-intel****.com.br`.

## Funcionalidades

- Gera combinações a partir de wordlists (palavras comuns, nomes, sobrenomes, variações numéricas)
- Resolve DNS em paralelo (ThreadPoolExecutor)
- Salva apenas os domínios que resolvem para um IP, com timestamp

## Como usar

1. Clone o repositório
2. Execute o script:
   ```bash
   python verifica.py
   
3. grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' ips_encontrados.txt > ips37777.txt
