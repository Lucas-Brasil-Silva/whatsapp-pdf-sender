# 🚀 Bot WhatsApp Sender - Automação de Envio de PDFs

Este projeto é uma ferramenta de automação desktop desenvolvida em Python para enviar arquivos PDF individualmente via WhatsApp Web. Possui uma Interface Gráfica (GUI) moderna construída com **Flet** e utiliza **Selenium** para a automação do navegador.

O sistema identifica o destinatário pelo nome do arquivo, busca o telefone correspondente em um CSV, envia o arquivo com uma mensagem personalizada e organiza os arquivos processados em pastas específicas.

## ✨ Funcionalidades

- **Interface Gráfica Amigável:** Painel de controle para digitar mensagens e acompanhar o progresso (Total, Sucessos, Erros).
- **Envio Automático:** Anexa PDFs e envia mensagens via WhatsApp Web.
- **Identificação Inteligente:** Lê o nome do arquivo (ex: `Holerite - JOAO.pdf`) para encontrar o contato correto.
- **Login Persistente:** Salva a sessão do WhatsApp (Cookies/Cache), exigindo o QR Code apenas na primeira execução.
- **Organização de Arquivos:** Move automaticamente os PDFs enviados para uma pasta de "Concluídos".
- **Logs em Tempo Real:** Console visual na aplicação informando cada etapa do processo.

## 🛠️ Tecnologias Utilizadas

- **[Python 3.x](https://www.python.org/)** - Linguagem base.
- **[Flet](https://flet.dev/)** - Framework para a Interface Gráfica (GUI).
- **[Selenium](https://www.selenium.dev/)** - Automação do navegador Chrome.
- **[Webdriver Manager](https://pypi.org/project/webdriver-manager/)** - Gerenciamento automático do driver do Chrome.
- **Pathlib** - Manipulação moderna de sistemas de arquivos.

## 📂 Estrutura do Projeto

```text
📁 projeto-raiz/
│
├── 📄 main.py               # Arquivo principal (Interface Gráfica e entrada do programa)
├── 📄 whatsapp_bot.py       # Lógica de automação com Selenium (Classe WhatsAppBot)
├── 📄 contatos.py           # Gerenciamento e leitura do CSV de contatos
├── 📄 file_organizer.py     # Utilitários para criar pastas, listar e mover arquivos
│
├── 📁 enviar_pdfs/          # (Criada automaticamente) Coloque os PDFs aqui
├── 📁 pdfs_enviados/        # (Criada automaticamente) Destino dos arquivos processados
└── 📄 Contatos Colaboradores.csv # (Criado automaticamente) Base de dados de telefones
```

## ⚙️ Pré-requisitos e Instalação

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/nome-do-repositorio.git](https://github.com/seu-usuario/nome-do-repositorio.git)
   cd nome-do-repositorio
   ```

2. **Crie um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   Executando o seguinte código:
   ```bash
   pip install requirements.txt
   ```

## 🚀 Como Usar

### 1. Configuração Inicial
Execute o programa pela primeira vez para que ele crie as pastas e arquivos necessários:
```bash
python main.py
```
O programa irá gerar:
- Uma pasta `enviar_pdfs` e  `pdfs_enviados`.
- Um arquivo `Contatos Colaboradores.csv`.

### 2. Preenchendo os Contatos
Abra o arquivo `Contatos Colaboradores.csv` gerado e preencha com os dados (mantenha o cabeçalho):

| Colaborador | Telefone |
| :--- | :--- |
| JOAO | 5511999999999 |
| MARIA | 5548988888888 |

> **Nota:** O telefone deve incluir o código do país (55 para Brasil), DDD o 9 e apenas números.

### 3. Regra de Nomeação dos Arquivos
Para que o robô saiba para quem enviar, o arquivo PDF deve seguir o padrão:
`Qualquer Coisa - NOME_DO_COLABORADOR.pdf`

O sistema pega tudo que está **após o último hífen** como o nome da pessoa.
- Exemplo: `Holerite Setembro - JOAO.pdf` -> O sistema buscará "JOAO" no CSV.
- Exemplo: `Aviso Ferias - MARIA.pdf` -> O sistema buscará "MARIA" no CSV.

### 4. Executando o Disparo
1. Coloque os arquivos PDF na pasta `enviar_pdfs`.
2. Abra o programa (`python main.py`).
3. Digite a mensagem que deseja enviar junto com o arquivo.
4. Clique em **INICIAR DISPARO**.
5. Se for a primeira vez, uma janela do Chrome abrirá pedindo para escanear o QR Code do WhatsApp. Nas próximas vezes, o login será automático.

## ⚠️ Avisos Legais e Limites

- Esta ferramenta utiliza automação de navegador simulando um usuário humano.
- **Evite Spam:** O WhatsApp possui sistemas anti-spam rigorosos. Utilize esta ferramenta com moderação, preferencialmente para contatos que já esperam receber essas mensagens (como colaboradores ou clientes ativos).
- Não nos responsabilizamos por bloqueios de números devido ao uso indevido da ferramenta.

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar Pull Requests.

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.