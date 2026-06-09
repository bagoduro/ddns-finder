import socket
import urllib.request
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ===== CONFIGURAÇÕES =====
PORTAS = [80, 37777, 9090, 8080]
TIMEOUT_PORTA = 0.3  # 300 ms para scan rápido

PALAVRAS_ESPECIFICAS = {
    'residencias': [
        "casa", "apartamento", "apto", "residencia", "moradia", "lar", "vila",
        "sobrado", "chacara", "sitio", "condominio", "jardim", "recanto", "refugio", "toca"
    ],
    'bares_e_hoteis': [
        "bar", "restaurante", "lanchonete", "pizzaria", "hotel", "pousada", "hostel", "flat",
        "eventos", "festa", "pub", "chopp", "cerveja"
    ],
    'lojas_roupas': [
        "loja", "roupas", "moda", "vestuario", "calcados", "sapatos", "camisas",
        "jeans", "feminino", "masculino", "infantil"
    ]
}

URL_WORDLIST = "https://raw.githubusercontent.com/pythonprobr/palavras/master/palavras.txt"
URL_NOMES = "https://raw.githubusercontent.com/arthuritas/wordlists/master/nomes.txt"
URL_SOBRENOMES = "https://raw.githubusercontent.com/arthuritas/wordlists/master/sobrenomes.txt"

FALLBACK_NOMES = [
    "joao", "maria", "jose", "ana", "pedro", "paulo", "lucas", "rafael", "carlos", "andre",
    "fernando", "ricardo", "juliana", "patricia", "renata", "marcos", "tiago", "bruno", "felipe"
]
FALLBACK_SOBRENOMES = [
    "silva", "santos", "oliveira", "souza", "pereira", "lima", "carvalho", "ferreira",
    "rodrigues", "alves", "gomes", "ribeiro", "costa", "martins", "araujo", "melo", "nascimento"
]

NOME_ARQUIVO_SAIDA = "ips_encontrados.txt"

# ===== FUNÇÕES =====

def sanitizar(subdominio):
    sub = re.sub(r'[^a-z0-9-]', '', subdominio.lower())
    sub = sub.strip('-')
    return sub

def baixar_lista(url, fallback_lista):
    try:
        with urllib.request.urlopen(url, timeout=10) as f:
            conteudo = f.read().decode('utf-8', errors='ignore')
            itens = [linha.strip().lower() for linha in conteudo.splitlines() if linha.strip()]
            if itens:
                return itens
    except Exception:
        pass
    return fallback_lista

def gerar_variacoes(palavra_base):
    palavra_sanitizada = sanitizar(palavra_base)
    if not palavra_sanitizada:
        return []
    variacoes = [palavra_sanitizada]
    for num in range(1, 10):
        variacoes.append(f"{palavra_sanitizada}{num}")
        variacoes.append(f"{palavra_sanitizada}{num:02d}")
        variacoes.append(f"{palavra_sanitizada}{num:03d}")
    return list(set(variacoes))

def gerar_nomes_sobrenomes(nomes, sobrenomes):
    combinacoes = []
    for nome in nomes[:50]:
        combinacoes.extend(gerar_variacoes(nome))
    for sob in sobrenomes[:50]:
        combinacoes.extend(gerar_variacoes(sob))
    for nome in nomes[:30]:
        for sob in sobrenomes[:30]:
            combinacoes.append(sanitizar(f"{nome}{sob}"))
            combinacoes.append(sanitizar(f"{nome}-{sob}"))
    for nome in nomes[:20]:
        for sob in sobrenomes[:20]:
            for num in range(1, 10):
                combinacoes.append(sanitizar(f"{nome}{sob}{num}"))
    return list(set(combinacoes))

def resolver_dominio(subdominio):
    dominio_completo = f"{subdominio}.ddns-intelbras.com.br"
    try:
        ip = socket.gethostbyname(dominio_completo)
        return dominio_completo, ip
    except (socket.gaierror, UnicodeError, UnicodeEncodeError):
        return None

def scan_portas(ip, portas, timeout=TIMEOUT_PORTA):
    abertas = []
    for porta in portas:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            resultado = sock.connect_ex((ip, porta))
            if resultado == 0:
                abertas.append(porta)
        except:
            pass
        finally:
            sock.close()
    return abertas

def salvar_resultado(dominio, ip, portas_abertas):
    with open(NOME_ARQUIVO_SAIDA, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {dominio} | {ip} | Portas: {portas_abertas}\n")

def main():
    print("--- GERADOR DE SUBDOMÍNIOS DDNS COM VERIFICAÇÃO RÁPIDA DE PORTAS (timeout 300ms) ---")
    
    open(NOME_ARQUIVO_SAIDA, 'w').close()
    print(f"Resultados serão salvos em: {NOME_ARQUIVO_SAIDA}\n")
    
    print("[1/4] Baixando listas...")
    palavras_gerais = baixar_lista(URL_WORDLIST, [])
    print(f"  -> Palavras gerais: {len(palavras_gerais)}")
    
    nomes = baixar_lista(URL_NOMES, FALLBACK_NOMES)
    sobrenomes = baixar_lista(URL_SOBRENOMES, FALLBACK_SOBRENOMES)
    print(f"  -> Nomes: {len(nomes)} | Sobrenomes: {len(sobrenomes)}")
    
    todas_palavras_base = set(palavras_gerais)
    for categoria, palavras in PALAVRAS_ESPECIFICAS.items():
        todas_palavras_base.update(palavras)
    
    palavras_validas = [p for p in todas_palavras_base if 3 <= len(p) <= 12]
    print(f"  -> Palavras-base (gerais + nichos): {len(palavras_validas)}")
    
    print("\n[2/4] Gerando subdomínios...")
    todos_subdominios = set()
    for palavra in palavras_validas[:1000]:
        todos_subdominios.update(gerar_variacoes(palavra))
    todos_subdominios.update(gerar_nomes_sobrenomes(nomes, sobrenomes))
    todos_subdominios = list(todos_subdominios)
    print(f"  -> Subdomínios únicos gerados: {len(todos_subdominios)}")
    
    print("\n[3/4] Resolvendo DNS e verificando portas rapidamente...")
    encontrados = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(resolver_dominio, sub): sub for sub in todos_subdominios}
        for i, future in enumerate(as_completed(futures)):
            resultado = future.result()
            if resultado:
                dominio, ip = resultado
                portas_abertas = scan_portas(ip, PORTAS)
                if portas_abertas:
                    print(f"[ENCONTRADO] {dominio} -> {ip} | Portas: {portas_abertas}")
                    salvar_resultado(dominio, ip, portas_abertas)
                    encontrados += 1
            if (i+1) % 500 == 0:
                print(f"Progresso DNS: {i+1}/{len(todos_subdominios)} | Encontrados com portas: {encontrados}")
    
    print(f"\n--- FINALIZADO ---")
    print(f"Total de IPs com pelo menos uma porta aberta: {encontrados}")
    print(f"Resultados salvos em '{NOME_ARQUIVO_SAIDA}' (domínio | IP | portas abertas).")

if __name__ == "__main__":
    main()
