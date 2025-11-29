# Guia de Deploy Gratuito 24/7

Como seu dashboard depende dos arquivos gerados pelo robô (relatórios, CSVs), o site e o robô precisam rodar **no mesmo lugar**. Serviços como Vercel ou Netlify não funcionam pois eles não têm acesso aos dados do seu robô.

Aqui estão as 2 melhores opções gratuitas:

## Opção 1: Cloudflare Tunnel (Mais Fácil)
*Ideal se você já deixa seu PC ligado 24/7.*
Expõe seu `localhost:5000` para a internet de forma segura (ex: `https://seu-projeto.trycloudflare.com`).

### Passo a Passo:
1. **Instale o Cloudflared:**
   ```bash
   # Linux
   curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared.deb
   ```

2. **Inicie o Túnel:**
   ```bash
   cloudflared tunnel --url http://localhost:5000
   ```
   *Copie o link que aparecerá no terminal.*

---

## Opção 2: Oracle Cloud Free Tier (Mais Profissional)
*Ideal para rodar 24/7 na nuvem sem depender do seu PC.*
A Oracle oferece uma VPS (computador na nuvem) muito potente e gratuita para sempre.

### Especificações Grátis:
- 4 CPUs (ARM Ampere)
- 24 GB de RAM
- 200 GB de Disco

### Passo a Passo:
1. Crie uma conta na [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/).
2. Crie uma instância **VM.Standard.A1.Flex** (escolha Ubuntu).
3. Conecte via SSH.
4. Clone seu repositório e configure o ambiente:
   ```bash
   git clone https://github.com/seu-usuario/seu-repo.git
   cd seu-repo
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Rode o dashboard em background (usando `tmux` ou `systemd`).

---

## Recomendação
Comece com o **Cloudflare Tunnel** para testar. Se precisar desligar o PC mas manter o site online, migre para a **Oracle Cloud**.
