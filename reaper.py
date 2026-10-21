import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import colorama
from colorama import Fore, Style
import sys
import time
import re
import json
import random
import difflib
from datetime import datetime

# Inicializa o colorama
colorama.init(autoreset=True)

# ==========================================
# CONFIGURAÇÕES DO MOTOR (WAF EVASION)
# ==========================================
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
]

SEVERITY_COLORS = {
    'CRITICAL': Fore.RED, 'HIGH': Fore.LIGHTRED_EX, 'MEDIUM': Fore.YELLOW, 
    'LOW': Fore.BLUE, 'SAFE': Fore.GREEN, 'INFO': Fore.CYAN
}

DOTS = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🔵', 'SAFE': '🟢', 'INFO': 'ℹ'}

class CyberReaperAsync:
    def __init__(self, target_url, concurrency=20):
        self.target_url = target_url
        self.domain = urlparse(target_url).netloc
        self.base_url = f"{urlparse(target_url).scheme}://{self.domain}"
        self.concurrency = concurrency
        
        # Limite de requisições simultâneas
        self.semaphore = asyncio.Semaphore(concurrency)
        
        self.results = {k: [] for k in SEVERITY_COLORS.keys()}
        self.scanned_urls = set()
        self.forms = []
        self.js_endpoints = set()
        
    def print_banner(self):
        banner = f"""
{Fore.RED}   ______      __              ____                     
  / ____/_  __/ /_  ___  _____/ __ \\___  ____ _____  _____
 / /   / / / / __ \\/ _ \\/ ___/ /_/ / _ \\/ __ `/ __ \\/ ___/
/ /___/ /_/ / /_/ /  __/ /  / _, _/  __/ /_/ / /_/ / /    
\\____/\\__, /_.___/\\___/_/  /_/ |_|\\___/\\__,_/ .___/_/     
     /____/                               /_/           {Style.RESET_ALL}
{Fore.CYAN} [ CyberReaper v7.0 - Async DAST Engine (Top 0.1%) ]{Style.RESET_ALL}
{Fore.MAGENTA}       "Eliminating False Positives. Securing the Web."{Style.RESET_ALL}
"""
        print(banner)

    def log(self, severity, owasp, title, details, url="", mitigation=""):
        finding = {"owasp": owasp, "title": title, "details": details, "url": url, "mitigation": mitigation}
        if finding not in self.results[severity]:
            self.results[severity].append(finding)
            dot = DOTS[severity]
            color = SEVERITY_COLORS[severity]
            print(f"  {color}{dot} [{title}]{Style.RESET_ALL} {details}")

    # ==========================================
    # FASE 1: CRAWLER ASSÍNCRONO E JS PARSER
    # ==========================================
    async def fetch(self, client, url):
        async with self.semaphore:
            try:
                # Delay aleatório para não acionar WAF
                await asyncio.sleep(random.uniform(0.1, 0.3))
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                return await client.get(url, headers=headers, timeout=10.0)
            except:
                return None

    async def deep_crawl(self, client, url, depth=1, max_depth=2):
        if depth > max_depth or url in self.scanned_urls: return
        self.scanned_urls.add(url)
        
        response = await self.fetch(client, url)
        if not response or response.status_code != 200: return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extrair Links HTML
        for a_tag in soup.find_all('a', href=True):
            link = urljoin(url, a_tag['href'])
            if self.domain in link and "#" not in link:
                asyncio.create_task(self.deep_crawl(client, link, depth + 1, max_depth))

        # Extrair Formulários
        for form in soup.find_all('form'):
            action = form.get('action', '')
            method = form.get('method', 'get').lower()
            inputs = [{'name': i.get('name'), 'type': i.get('type', 'text')} for i in form.find_all('input') if i.get('name')]
            if inputs:
                self.forms.append({'action': urljoin(url, action), 'method': method, 'inputs': inputs})

        # EXTRAIR ENDPOINTS DO JAVASCRIPT (O Segredo para SPAs)
        for script in soup.find_all('script', src=True):
            if self.domain in script['src']:
                js_url = urljoin(url, script['src'])
                js_res = await self.fetch(client, js_url)
                if js_res:
                    # Regex para achar rotas de API no JS (ex: /api/v1/users)
                    endpoints = re.findall(r'["\'](/api/[a-zA-Z0-9_\-/]+)["\']', js_res.text)
                    for ep in endpoints:
                        self.js_endpoints.add(urljoin(self.base_url, ep))

    # ==========================================
    # FASE 2: MOTOR DE VALIDAÇÃO E INJEÇÃO
    # ==========================================
    
    # PAYLOADS DE EVASÃO DE WAF (Poliglotas)
    PAYLOADS = {
        'XSS': ['<script>alert(1)</script>', '<img src=x onerror=alert(1)>', '<svg/onload=alert(1)>', '"><script>alert(1)</script>'],
        'SQLi': ["'", "admin' AND '1'='1", "admin' AND '1'='2", "admin'/**/OR/**/1=1--"],
        'SSTI': ["{{7*7}}", "${7*7}", "<%= 7*7 %>"],
        'CMDi': ["; id", "| id", "`id`", "127.0.0.1; sleep 5"]
    }

    async def test_injections(self, client, form):
        base_data = {inp['name']: "test" for inp in form['inputs']}
        if not base_data: return

        # 1. Validação de CSRF
        if form['method'] == 'post':
            has_token = any('csrf' in str(inp['name']).lower() or 'token' in str(inp['name']).lower() for inp in form['inputs'])
            if not has_token:
                self.log('MEDIUM', 'A01:2021', 'Falta de Token CSRF', f"Form POST sem proteção CSRF.", form['action'], "Implemente tokens anti-CSRF sincronizados.")

        # 2. Teste XSS Contextual
        for payload in self.PAYLOADS['XSS']:
            data = {k: payload for k in base_data}
            res = await self.fetch_post(client, form, data)
            if res and payload in res.text and "&lt;script&gt;" not in res.text:
                self.log('CRITICAL', 'A03:2021', 'XSS Confirmado', f"Payload executável refletido.", form['action'], "Use htmlentities() no PHP ou escape de contextos no front-end.")
                break # Para de testar se já achou

        # 3. Teste SQLi Boolean-Based (O Fim dos Falsos Positivos)
        data_true = {k: self.PAYLOADS['SQLi'][1] for k in base_data}
        data_false = {k: self.PAYLOADS['SQLi'][2] for k in base_data}
        
        res_true = await self.fetch_post(client, form, data_true)
        res_false = await self.fetch_post(client, form, data_false)
        
        if res_true and res_false:
            # Usa difflib para ver a similaridade real do HTML
            similarity = difflib.SequenceMatcher(None, res_true.text, res_false.text).ratio()
            if similarity < 0.90: # Se a página mudou mais de 10%, é real
                self.log('CRITICAL', 'A03:2021', 'SQL Injection (Boolean)', "Mudança estrutural confirmada entre 1=1 e 1=2.", form['action'], "Use Prepared Statements / Parametrized Queries.")

        # 4. Teste Command Injection Time-Based
        data_cmdi = {k: self.PAYLOADS['CMDi'][3] for k in base_data}
        start = time.time()
        await self.fetch_post(client, form, data_cmdi, timeout=10.0)
        if time.time() - start > 4.5:
             self.log('CRITICAL', 'A03:2021', 'Command Injection', "Time-based delay detectado.", form['action'], "Nunca passe inputs do usuário para funções como exec() ou system().")

    async def fetch_post(self, client, form, data, timeout=5.0):
        async with self.semaphore:
            try:
                if form['method'] == 'post':
                    return await client.post(form['action'], data=data, timeout=timeout)
                else:
                    return await client.get(form['action'], params=data, timeout=timeout)
            except:
                return None

    # ==========================================
    # FASE 3: ANÁLISE DE CONFIGURAÇÃO (A05)
    # ==========================================
    async def check_misconfigurations(self, client):
        print(f"\n{Fore.CYAN}[*] Analisando Configurações de Servidor (A05)...{Style.RESET_ALL}")
        res = await self.fetch(client, self.target_url)
        if not res: return
        
        headers = res.headers
        missing = [h for h in ['Content-Security-Policy', 'X-Frame-Options', 'X-Content-Type-Options'] if h not in headers]
        if missing:
            self.log('MEDIUM', 'A05:2021', 'Headers Ausentes', f"Faltando: {', '.join(missing)}", self.target_url, "Adicione headers de segurança no Nginx/Apache.")
            
        if 'X-Powered-By' in headers:
            self.log('LOW', 'A05:2021', 'Information Disclosure', f"Vazando tecnologia: {headers['X-Powered-By']}", self.target_url, "Desative a flag expose_php ou remova o header X-Powered-By.")

    # ==========================================
    # FASE 4: GERADOR DE RELATÓRIO HTML PREMIUM
    # ==========================================
    def generate_report(self):
        print(f"\n{Fore.CYAN}[*] Construindo Relatório de Nível Executivo...{Style.RESET_ALL}")
        filename = f"pentest_{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        total_vulns = sum(len(self.results[k]) for k in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pentest Report - {self.domain}</title>
            <style>
                body {{ background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; }}
                h1 {{ color: #58a6ff; text-align: center; }}
                .summary {{ display: flex; justify-content: space-between; background: #161b22; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
                .box {{ text-align: center; }}
                .box h2 {{ margin: 0; font-size: 36px; }}
                .critical {{ color: #f85149; }} .high {{ color: #d29922; }} .medium {{ color: #f2cc60; }} .low {{ color: #3fb950; }}
                table {{ width: 100%; border-collapse: collapse; background: #161b22; border-radius: 10px; overflow: hidden; }}
                th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #30363d; }}
                th {{ background: #1f2428; color: #58a6ff; }}
                .mitigation {{ color: #3fb950; font-style: italic; font-size: 13px; }}
            </style>
        </head>
        <body>
            <h1>CyberReaper v7.0 - Enterprise Pentest Report</h1>
            <p><strong>Alvo:</strong> {self.target_url} | <strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            
            <div class="summary">
                <div class="box"><h2 class="critical">{len(self.results['CRITICAL'])}</h2><p>Crítico</p></div>
                <div class="box"><h2 class="high">{len(self.results['HIGH'])}</h2><p>Alto</p></div>
                <div class="box"><h2 class="medium">{len(self.results['MEDIUM'])}</h2><p>Médio</p></div>
                <div class="box"><h2 class="low">{len(self.results['LOW'])}</h2><p>Baixo</p></div>
            </div>
            
            <table>
                <tr><th>Severidade</th><th>OWASP</th><th>Vulnerabilidade</th><th>Detalhes / URL</th><th>Como Mitigar</th></tr>
        """
        
        for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            for item in self.results[sev]:
                color_class = sev.lower()
                html += f"""
                <tr>
                    <td class="{color_class}"><strong>{sev}</strong></td>
                    <td>{item['owasp']}</td>
                    <td>{item['title']}</td>
                    <td>{item['details']}<br><small style="color:#8b949e;">{item['url']}</small></td>
                    <td class="mitigation">{item['mitigation']}</td>
                </tr>
                """
                
        html += "</table></body></html>"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
            
        print(f"{Fore.GREEN}  [+] Relatório salvo em: {filename}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  [i] Encontradas {total_vulns} vulnerabilidades ativas.{Style.RESET_ALL}")

    # ==========================================
    # EXECUÇÃO PRINCIPAL (ASSÍNCRONA)
    # ==========================================
    async def run(self):
        self.print_banner()
        
        async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
            print(f"{Fore.YELLOW}[*] Iniciando Crawler Assíncrono e Extração de JS...{Style.RESET_ALL}")
            await self.deep_crawl(client, self.target_url, depth=1, max_depth=2)
            
            print(f"{Fore.YELLOW}[*] Mapeamento concluído: {len(self.scanned_urls)} URLs | {len(self.forms)} Forms | {len(self.js_endpoints)} APIs (JS){Style.RESET_ALL}")
            
            await self.check_misconfigurations(client)
            
            print(f"\n{Fore.CYAN}[*] Disparando Motor de Injeção (Concorrência: {self.concurrency})...{Style.RESET_ALL}")
            tasks = [self.test_injections(client, form) for form in self.forms]
            await asyncio.gather(*tasks)
            
            self.generate_report()

if __name__ == "__main__":
    print(Fore.CYAN + "\nDigite a URL do alvo: ")
    target = input("> ").strip()
    if not target.startswith("http"):
        target = "http://" + target
    
    scanner = CyberReaperAsync(target, concurrency=15)
    asyncio.run(scanner.run())
